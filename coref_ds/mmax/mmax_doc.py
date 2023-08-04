
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from lxml import etree
from lxml.etree import _Element

from pathlib import Path
from coref_ds.document import CorefDoc
from coref_ds.mmax.markable import Markable
from coref_ds.mmax.word import Word
from coref_ds.text import Text, Segment

NSMAP = {
    'xlmns': 'www.eml.org/NameSpaces/mention'
}

@dataclass
class MmaxFiles:
    mmax: _Element
    mentions:_Element
    words:_Element
    bak_mentions:_Element = None


class MmaxDoc(CorefDoc):
    def __init__(self, doc_id: str, words: list[Word], mentions: list[Markable]):
        self.doc_id = doc_id
        self.words = words
        self.mentions = mentions

    @staticmethod
    def load_files(p: Path):
        doc_id = p.stem
        bak_mentions_path = p.parent / f'{doc_id}_mentions.xml.bak'
        if bak_mentions_path.exists():
            bak_mentions = etree.parse(bak_mentions_path)
        else:
            bak_mentions = None

        return MmaxFiles(
            mmax=etree.parse(p),
            mentions=etree.parse(p.parent / f'{doc_id}_mentions.xml'),
            words=etree.parse(p.parent / f'{doc_id}_words.xml'),
            bak_mentions=bak_mentions
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

    def to_file(self, filename: Path):
        pass  # @TODO

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
        clusters = defaultdict(set)
        for m in self.mentions:
            span = m.get_span()
            if span:
                cluster_id = m.mention_group if m.mention_group != 'empty' else m.id
                clusters[cluster_id].add(span)

        segments_meta = []
        for word in self.words:
            segments_meta.append(word)

        return Text(
            self.doc_id,
            [w.orth for w in self.words],
            segments_meta,
            list(clusters.values()),
        )
