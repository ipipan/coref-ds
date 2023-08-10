from typing import DefaultDict

import regex
from coref_ds.tei.utils import remove_if_no_children
from coref_ds.tei.layers.layer import XMLLayer

XML_NS = 'http://www.w3.org/XML/1998/namespace'

class MorphosyntaxLayer(XMLLayer):
    """
    Class for loading morphosyntax layer from NKJP TEI format.
    """

    @staticmethod
    def get_gender(msd):
        tags = msd.split(':')
        if 'm1' in tags:
            return 'm1'
        elif 'm2' in tags:
            return 'm2'
        elif 'm3' in tags:
            return 'm3'
        elif 'f' in tags:
            return 'f'
        elif 'n' in tags:
            return 'n'
        else:
            return 'unk'

    @staticmethod
    def get_person(msd):
        tags = msd.split(':')
        if 'pri' in tags:
            return 'pri'
        elif 'sec' in tags:
            return 'sec'
        elif 'ter' in tags:
            return 'ter'
        else:
            return 'unk'

    @staticmethod
    def get_number(msd):
        tags = msd.split(':')
        if 'sg' in tags:
            return 'sg'
        elif 'pl' in tags:
            return 'pl'
        else:
            return 'unk'

    @staticmethod
    def parse_interpretation(interpretation):
        split = interpretation.split(':')
        if interpretation.startswith(':'):
            base = ':'
            ctag = 'interp'
            msd = ''
        elif len(split) > 2:
            base = split[0]
            ctag = split[1]
            msd = ':'.join(split[2:])
        else:
            base = split[0]
            ctag = split[1]
            msd = ''
        return base, ctag, msd

    @staticmethod
    def get_feature_string(f):
        return f.getchildren()[0].text

    @staticmethod
    def get_f_bin_value(f):
        value = False
        if f.getchildren()[0].attrib['value'] == 'true':
            value = True
        return value

    @staticmethod
    def read_segment(seg, last_in_sent, last_in_paragraph, ns_map):
        has_nps = False
        base = ''
        ctag = ''
        msd = ''
        orth = ''
        idx = seg.attrib[f'{{{XML_NS}}}id']
        for morph_feature in seg.xpath(".//tei:f", namespaces=ns_map):
            if morph_feature.attrib['name'] == 'orth':
                orth = MorphosyntaxLayer.get_feature_string(morph_feature)
            elif morph_feature.attrib['name'] == 'nps':
                has_nps = MorphosyntaxLayer.get_f_bin_value(morph_feature)
            elif morph_feature.attrib['name'] == 'interpretation':
                interpretation = MorphosyntaxLayer.get_feature_string(morph_feature)
                (base, ctag, msd) = MorphosyntaxLayer.parse_interpretation(interpretation)
        return {
            'id': idx,
            'orth': orth,
            'base': base,
            'has_nps': has_nps,
            'last_in_sent': last_in_sent,
            'last_in_par': last_in_paragraph,
            'ctag': ctag,
            'msd': msd,
            'number': MorphosyntaxLayer.get_number(msd),
            'person': MorphosyntaxLayer.get_person(msd),
            'gender': MorphosyntaxLayer.get_gender(msd)
        }

    @property
    def segment_nodes(self):
        paragraphs = self.root.xpath(".//tei:p", namespaces=self.ns_map)
        n_paragraphs = len(paragraphs)
        for par_id, par in enumerate(paragraphs):
            sentences = par.xpath(".//tei:s", namespaces=self.ns_map)
            n_sentences = len(sentences)
            for sent_id, sent in enumerate(sentences):
                segments = sent.xpath(".//tei:seg", namespaces=self.ns_map)
                n_segments = len(segments)
                for seg_ind, seg in enumerate(segments):
                    last_in_sent = False
                    last_in_paragraph = False
                    if seg_ind == n_segments - 1:
                        last_in_sent = True
                        if sent_id == n_sentences - 1:
                            last_in_paragraph = True
                    yield {
                        'seg': seg,
                        'seg_id': seg_ind,
                        'sent_id': sent_id,
                        'sent': sent,
                        'par': par,
                        'last_in_sent': last_in_sent,
                        'last_in_paragraph': last_in_paragraph,
                        'n_paragraphs': n_paragraphs,
                    }

    def parse_layer(self):
        segments_dict = {}
        segments_ids = []
        for segment_node in self.segment_nodes:
            seg, last_in_sent, last_in_paragraph = segment_node['seg'], segment_node['last_in_sent'], segment_node[
                'last_in_paragraph']
            segment = MorphosyntaxLayer.read_segment(seg, last_in_sent, last_in_paragraph, self.ns_map)
            segments_dict[segment['id']] = segment
            segments_ids.append(segment['id'])

        return {
            'segments_dict': segments_dict,
            'segments_ids': segments_ids,
        }

    def filter_by_sample_ids(self, sample_ids):
        for segment_node in self.segment_nodes:
            seg = segment_node['seg']
            segment_id = seg.attrib[f'{{{self.ns_map["xmlns"]}}}id']
            if segment_id not in sample_ids:
                parent = seg.getparent()
                parent.remove(segment_node['seg'])
                remove_if_no_children(parent, levels=2)

    @staticmethod
    def get_sample_id(segment):
        """<seg corresp="ann_segmentation.xml#segm_1.1-seg" xml:id="morph_1.1-seg">"""
        # write a regex to catch the "txt_1.2-ab" from the line above

        corresp = segment.attrib['corresp']

        sample_id = regex.match(r'ann_segmentation.xml#(.+)', corresp).group(1)
        return sample_id

    @property
    def morphosyntax_mapping(self):
        mapping = DefaultDict(list)
        for segment_node in self.segment_nodes:
            seg = segment_node['seg']
            morphosyntax_id = seg.attrib[f'{{{self.ns_map["xmlns"]}}}id']
            segment_id = self.get_sample_id(seg)
            mapping[segment_id].append(morphosyntax_id)

        return mapping
