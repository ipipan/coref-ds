# ---------------------------------------------------------------------------------------------------------------------
# TEI format parser based on:
# - http://zil.ipipan.waw.pl/Corneferencer
# - http://git.nlp.ipipan.waw.pl/cothec/Corneferencer
# ---------------------------------------------------------------------------------------------------------------------


import gzip
import shutil
import os
import logging
from pathlib import Path
from collections import defaultdict
from typing import Callable
from abc import ABC, abstractmethod


import regex
from lxml import etree
from lxml.etree import _Comment as Comment
import yaml

from coref_ds.tei.layers.coreference import CoreferenceLayer
from coref_ds.tei.layers.layer import XMLLayer
from coref_ds.tei.layers.mention import MentionLayer
from coref_ds.tei.layers.morphosyntax import MorphosyntaxLayer
from coref_ds.tei.layers.segmentation import SegmentationLayer
from coref_ds.tei.nkjp import NKJPStructureLayer
from coref_ds.tei.utils import get_file_or_archive, word_to_ignore

from coref_ds.text import Segment, Text

logger = logging.getLogger(__name__)

NKJP_NS = 'http://www.nkjp.pl/ns/1.0'
TEI_NS = 'http://www.tei-c.org/ns/1.0'
XI_NS = 'http://www.w3.org/2001/XInclude'
XML_NS = 'http://www.w3.org/XML/1998/namespace'

NSMAP = {
    'xmlns': XML_NS,
    'tei': TEI_NS,
    'nkjp': NKJP_NS,
    'xi': XI_NS,
}


class TEIDocument:
    def __init__(
            self,
            doc_path: Path,
            layers_mapping: dict = None,
            text_structure_name: str = 'text',
            ns_map: dict = NSMAP
    ):
        if layers_mapping is None:
            layers_mapping = {
                'text_structure': (NKJPStructureLayer, text_structure_name),
                'coreference': (CoreferenceLayer, 'ann_coreference'),
                'groups': (None, 'ann_groups'),
                'mentions': (MentionLayer, 'ann_mentions'),
                'morphosyntax': (MorphosyntaxLayer, 'ann_morphosyntax'),
                'named_entities': (None, 'ann_named'),
                'segmentation': (SegmentationLayer, 'ann_segmentation'),
                'senses': (None, 'ann_senses'),
            }
        self.layers_mapping = layers_mapping
        self.doc_path = doc_path
        self.ns_map = ns_map
        self.layers = self.load_layers()
        self.splitter = LayersSplitter(self)

    def load_layers(self):
        layers = {}
        for layer_name, (layer_class, layer_path) in self.layers_mapping.items():
            p = get_file_or_archive(self.doc_path / layer_path)
            layer_class = layer_class if layer_class else XMLLayer
            if p is not None:
                layers[layer_name] = layer_class(p, self.ns_map)

        return layers

    def parse_tei_text(self, add_single_mentions_to_cluster=False):
        morph_dict = self.layers['morphosyntax'].parse_layer()
        segments_ids, segments_dict = morph_dict['segments_ids'], morph_dict['segments_dict']
        segments = [segment['orth'] for k, segment in segments_dict.items()]
        segments_dicts = [segment for k, segment in segments_dict.items()]
        segments_meta = {
            segment['id']: Segment(
                id=segment['id'],
                orth=segment['orth'],
                lemma=segment['base'],
                has_nps=segment['has_nps'],
                last_in_sent=segment['last_in_sent'],
                last_in_par=segment['last_in_par'],
                pos=segment['ctag'],
                number=segment['number'],
                person=segment['person'],
                gender=segment['gender'],
            ) for segment in segments_dicts
        }
        if self.layers.get('mentions'):
            mentions = self.layers['mentions'].parse_layer(segments_meta, segments_ids)

        text = Text(
            self.doc_path.name,
            segments,
            list(segments_meta.values()),
            clusters=None,
        )
        text.mentions = mentions
        text.indices_to_mentions = {(m.span_start, m.span_end): m for m in mentions}

        if self.layers.get('coreference'):
            mention_clusters = self.layers['coreference'].parse_layer()
            self.layers['coreference'].add_clusters_to_text(mention_clusters, text)
            mentions_sets = defaultdict(list)

            for mention in text.mentions:
                if mention.cluster_id:
                    key = mention.cluster_id
                elif add_single_mentions_to_cluster:
                    key = mention.id
                else:
                    key = None

                if key:
                    mentions_sets[key].append(
                        (mention.span_start, mention.span_end)
                    )

            text.clusters = list(mentions_sets.values())
            
        return text

    @property
    def text(self, add_single_mentions_to_cluster=True):
        return self.parse_tei_text(add_single_mentions_to_cluster)


    def to_file(self, filedir: Path):
        for layer in self.layers.values():
            layer.to_file(filedir)

    @property
    def is_single_sample(self) -> bool:
        text_structure = self.layers['text_structure'].parse_layer()
        if len(text_structure['divs']) == 1:
            return True
        else:
            return False

    def split(self, cum_call: Callable = None):
        def append_to(el):
            rt.append(el)

        if not cum_call:
            rt = []
            cum_call = append_to
            self.splitter.get_continuous_samples(cum_call)
            return rt
        else:
            self.splitter.get_continuous_samples(cum_call)
            return None


def write(input_path, output_path, text):
    output_path = Path(output_path)

    if not output_path.exists():
        os.mkdir(output_path)

    for filename in os.listdir(input_path):
        if not filename.startswith('ann_coreference'):
            layer_in_path = input_path / filename
            layer_out_path = output_path / filename
            copy_layer(layer_in_path, layer_out_path)

    coref_out_path = os.path.join(output_path, 'ann_coreference.xml.gz')
    write_coreference(coref_out_path, text)


def copy_layer(src, dest):
    shutil.copyfile(src, dest)


def write_coreference(outout_path, text):
    root, tei = write_header()
    write_body(tei, text)

    with gzip.open(outout_path, 'wb') as output_file:
        output_file.write(etree.tostring(root, pretty_print=True,
                                         xml_declaration=True, encoding='UTF-8'))


def write_header():
    root = etree.Element('teiCorpus', nsmap=NSMAP)

    corpus_xinclude = etree.SubElement(root, etree.QName(XI_NS, 'include'))
    corpus_xinclude.attrib['href'] = 'PCC_header.xml'

    tei = etree.SubElement(root, 'TEI')
    tei_xinclude = etree.SubElement(tei, etree.QName(XI_NS, 'include'))
    tei_xinclude.attrib['href'] = 'header.xml'

    return root, tei


def write_body(tei, text):
    text_node = etree.SubElement(tei, 'text')
    body = etree.SubElement(text_node, 'body')
    p = etree.SubElement(body, 'p')

    sets = text.get_sets()
    for set_id in sets:
        comment_text = create_set_comment(sets[set_id])
        p.append(etree.Comment(comment_text))

        seg = etree.SubElement(p, 'seg')
        seg.attrib[etree.QName(XML_NS, 'id')] = set_id.replace('set', 'coreference')

        fs = etree.SubElement(seg, 'fs')
        fs.attrib['type'] = 'coreference'

        f_type = etree.SubElement(fs, 'f')
        f_type.attrib['name'] = 'type'
        f_type.attrib['fVal'] = 'ident'

        dominant = get_dominant(sets[set_id])
        f_dominant = etree.SubElement(fs, 'f')
        f_dominant.attrib['name'] = 'dominant'
        f_dominant.attrib['fVal'] = dominant

        for mnt in sets[set_id]:
            ptr = etree.SubElement(seg, 'ptr')
            ptr.attrib['target'] = 'ann_mentions.xml#%s' % mnt.id


class LayersSplitter:
    def __init__(self, tei_doc: TEIDocument):
        self.segmentation_mapping = None
        self.tei_doc = tei_doc

    def get_continuous_samples(self, cum_call: Callable):
        continuous_parts = list(self.tei_doc.layers['text_structure'].continuous_excerpts)
        for sample_idx, sample_group in enumerate(continuous_parts):
            subdoc = TEIDocument(self.tei_doc.doc_path)
            sample_ids = set(
                sample['sample_id'] for sample in sample_group
            )
            self.filter_by_sample_ids(subdoc, sample_ids)
            # this is much slower (quadratically) for long texts because
            # it is repeated each time for all samples in the text (for each sample)
            # however, it is xml format agnostic (at least in a way)
            debug = subdoc.layers['text_structure'].parse_layer()
            cum_call(subdoc, sample_idx)

    def filter_by_sample_ids(self, subdoc: TEIDocument, sample_ids: set[str]):
        custom_filtered_layers = ('text_structure', 'segmentation', 'morphosyntax')

        subdoc.layers['text_structure'].filter_by_sample_ids(sample_ids)
        segmentation_mapping = subdoc.layers['segmentation'].segmentation_mapping
        segmentation_mapped_ids = set(
            segment_id for sample_id in sample_ids for segment_id in segmentation_mapping[sample_id]
        )
        subdoc.layers['segmentation'].filter_by_sample_ids(sample_ids)
        morphosyntax_mapping = subdoc.layers['morphosyntax'].morphosyntax_mapping
        morphosyntax_mapped_ids = set(
            morph_id for el in segmentation_mapped_ids for morph_id in morphosyntax_mapping[el]
        )
        subdoc.layers['morphosyntax'].filter_by_sample_ids(morphosyntax_mapped_ids)

        for layer_name, layer in subdoc.layers.items():
            if layer_name in custom_filtered_layers:
                continue
            elif hasattr(layer, 'filter_by_sample_ids'):
                layer.filter_by_sample_ids(sample_ids)


def create_set_comment(mentions):
    mentions_orths = [mnt.text for mnt in mentions]
    mentions_orths = '; '.join(mentions_orths)
    return f'  {mentions_orths}  '


def get_dominant(mentions):
    longest_mention = mentions[0]
    for mnt in mentions:
        if len(mnt.words) > len(longest_mention.words):
            longest_mention = mnt
    return longest_mention.text


def write_samples(doc: TEIDocument, out_dir: Path):
    doc.split(lambda sample, sample_ind: sample.to_file(out_dir / f'{doc.doc_path.name}_{sample_ind}'))
