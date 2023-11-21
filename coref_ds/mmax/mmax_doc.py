from collections import defaultdict
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from lxml import etree
from lxml.etree import _Element

from coref_ds.document import CorefDoc
from coref_ds.mmax.markable import Markable, gen_mentions_structure
from coref_ds.mmax.word import Word, gen_words_structure
from coref_ds.text import Text, Segment
from coref_ds.utils import add_element


NSMAP = {'xlmns': 'www.eml.org/NameSpaces/mention'}


@dataclass
class MmaxFiles:
    mmax: _Element
    mentions: _Element
    words: _Element
    bak_mentions: _Element = None  # These rather just a backup file


def gen_mmax_schema(doc_id):
    schema = f"""<?xml version="1.0" standalone="no"?>
    <mmax_project>
    <words>{doc_id}_words.xml</words>
    <title val=""/>
    <catRef val=""/>
    </mmax_project>"""
    xml = etree.parse(StringIO(schema))

    return xml


def add_cluster_mentions(text: Text):
    mentions = []
    men_id = 0
    if text is not None:
        for cluster_id, cluster in enumerate(text.clusters):
            if len(cluster.mentions) == 1:
                cluster_id = 'empty'
            else:
                cluster_id = f'set_{str(cluster_id)}'

            for mention in cluster.mentions:
                men_id += 1

                head = mention.head if getattr(mention, 'head', None) else None
                m = Markable(
                    cluster_id=cluster_id,
                    men_id=f'markable_{men_id}',
                    span_start=mention.org_inds[0],
                    span_end=mention.org_inds[1],
                    head=head,
                )
                mentions.append(m)
    return mentions


def write_mmax_schema(mmax_schema: etree._Element, doc_id: str, doc_dir: Path):
    with open(Path(doc_dir) / f'{doc_id}.mmax', 'wb') as output_file:
        output_file.write(
            etree.tostring(
                mmax_schema, pretty_print=True, xml_declaration=True, encoding='utf-8'
            )
        )


class MmaxDoc(CorefDoc):
    def __init__(self, doc_id: str, words: list[Word], mentions: list[Markable]):
        self.doc_id = doc_id
        self.words = words
        self.mentions = mentions

    @staticmethod
    def load_files(p: Path, load_bak_mentions: bool = False):
        doc_id = p.stem
        mentions_path = p.parent / f'{doc_id}_mentions.xml'
        bak_mentions_path = p.parent / f'{doc_id}_mentions.xml.bak'

        if bak_mentions_path.exists() and load_bak_mentions:
            bak_mentions = etree.parse(bak_mentions_path)
        else:
            bak_mentions = None

        return MmaxFiles(
            mmax=etree.parse(p),
            mentions=etree.parse(mentions_path),
            words=etree.parse(p.parent / f'{doc_id}_words.xml'),
            bak_mentions=bak_mentions,
        )

    @classmethod
    def from_file(cls, filename: Path, mmax_files: MmaxFiles = None):
        doc_id = filename.stem

        if mmax_files is None:
            mmax_files = cls.load_files(filename)

        words = cls.parse_words(mmax_files.words)
        mentions = cls.parse_mentions(mmax_files.mentions)
        if mmax_files.bak_mentions:
            mentions.extend(cls.parse_mentions(mmax_files.bak_mentions))
        return cls(doc_id, words, mentions)

    def to_file(self, dir: Path):
        mmax_files = MmaxFiles(
            mmax=gen_mmax_schema(self.doc_id),
            mentions=gen_mentions_structure(),
            words=gen_words_structure(),
        )
        for word_id, word in enumerate(self.words):
            word.to_xml(mmax_files.words.getroot(), word_id)

        for mention_id, mention in enumerate(self.mentions):
            mention.to_xml(mmax_files.mentions.getroot())

        with open(Path(dir) / f'{self.doc_id}_words.xml', 'wb') as output_file:
            output_file.write(
                etree.tostring(
                    mmax_files.words, pretty_print=True, xml_declaration=True, encoding='utf-8'
                )
            )
        with open(Path(dir) / f'{self.doc_id}_mentions.xml', 'wb') as output_file:
            output_file.write(
                etree.tostring(
                    mmax_files.mentions, pretty_print=True, xml_declaration=True, encoding='utf-8'
                )
            )
        write_mmax_schema(mmax_files.mmax, self.doc_id, dir)

    @staticmethod
    def parse_words(words_tree: etree._Element):
        root = words_tree.getroot()
        words = []
        for word in root.findall('word'):
            words.append(Word.from_xml(word))
        return words

    @staticmethod
    def parse_mentions(mentions_tree: etree._Element, namespace: dict = NSMAP):
        mentions = []
        for markable in mentions_tree.xpath('xlmns:markable', namespaces=namespace):
            mentions.append(Markable.from_xml(markable))
        return mentions

    @property
    def text(self):
        clusters = defaultdict(list)
        for m in self.mentions:
            span = m.get_span()
            if span:
                cluster_id = m.mention_group if m.mention_group != 'empty' else m.id
                clusters[cluster_id].append(span)

        segments_meta = []
        for word in self.words:
            segments_meta.append(word)

        return Text(
            text_id=self.doc_id,
            segments=[w.orth for w in self.words],
            segments_meta=segments_meta,
            clusters=list(clusters.values()),
        )
