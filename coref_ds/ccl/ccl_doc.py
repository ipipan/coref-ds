from pathlib import Path
import logging

from lxml import etree as ET

from coref_ds.text import Text, SegmentMeta



class CclDoc:
    def __init__(self, p: Path):
        self.doc_path = p
        self._clusters = None
        self.xml = ET.parse(p)
        self._parse_ccl()


    def _parse_ccl(self):
        segments = []
        segments_meta = []
        clusters = []  # assume it's empty
        for sentence in self.xml.xpath('//sentence'):
            sent_tokens = list(sentence.xpath('tok'))

            for ind, segment in enumerate(sent_tokens):
                try:
                    segments.append(segment.xpath('orth/text()')[0])
                    segment_meta = SegmentMeta(
                        orth=segment.xpath('orth/text()')[0],
                        pos=segment.xpath('lex/ctag/text()')[0],
                        lemma=segment.xpath('lex/base/text()')[0],
                        has_nps=False,
                        last_in_sent= True if ind == len(sent_tokens) - 1 else False,
                    )
                    segments_meta.append(segment_meta)
                except Exception as e:
                    logging.error(f'Error while parsing segment {segment} in {self.doc_path}')
                    logging.exception(e)
            
        self.segments = segments
        self.segments_meta = segments_meta
        self.clusters = clusters

    @property
    def text(self):
        return Text(
            text_id=self.doc_path.stem,
            segments=self.segments,
            segments_meta=self.segments_meta,
            clusters=self.clusters,
        )