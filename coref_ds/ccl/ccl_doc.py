from pathlib import Path
import logging

from lxml import etree as ET

from coref_ds.text import Text, Segment



class CclSegment(Segment):
    def __init__(
            self,
            orth: str,
            pos: str,
            lemma: str,
            has_nps: bool,
            last_in_sent: bool
        ):
            super().__init__(
                orth,
                lemma,
                has_nps,
                last_in_sent,
                pos=pos,
            )

    @classmethod
    def from_xml(cls, xml_token: ET._Element, last_in_sent: bool):
        return cls(
                    orth=str(xml_token.xpath('orth/text()')[0]) if xml_token.xpath('orth/text()') else '',
                    pos=str(xml_token.xpath('lex/ctag/text()')[0]) if xml_token.xpath('lex/ctag/text()') else '',
                    lemma=str(xml_token.xpath('lex/base/text()')[0]) if xml_token.xpath('lex/base/text()') else '',
                    has_nps=False,
                    last_in_sent=last_in_sent,
        )

    def __str__(self):
        return self.orth


class CclDoc:
    def __init__(self, doc_id: str, segments: list[CclSegment], clusters: list[list[tuple[int, int]]]):
        self.doc_id = doc_id
        self.segments = segments
        self.clusters = clusters

    @classmethod
    def from_file(cls, p: Path):
        xml = ET.parse(p)
        print(xml)
        segments, clusters = cls._parse_ccl(xml, p)
        return cls(p.stem, segments, clusters)

    @staticmethod
    def _parse_ccl(xml, doc_path: Path):
        segments = []
        clusters = []  # assume it's empty @TODO: implement
        for sentence in xml.xpath('//sentence'):
            sent_tokens = list(sentence.xpath('tok'))

            for ind, segment in enumerate(sent_tokens):
                try:
                    last_in_sent = True if ind == len(sent_tokens) - 1 else False
                    segment = CclSegment.from_xml(segment, last_in_sent)
                    segments.append(segment)
                except Exception as e:
                    logging.error(f'Error while parsing segment {segment} in {doc_path}')
                    logging.exception(e)
            
        return segments, clusters

    @property
    def text(self):
        return Text(
            text_id=self.doc_id,
            segments=list( str(seg) for seg in self.segments),
            segments_meta=self.segments,
            clusters=self.clusters,
        )