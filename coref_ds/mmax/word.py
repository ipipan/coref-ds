from dataclasses import dataclass

from lxml import etree

from coref_ds.text import Segment


@dataclass
class Word(Segment):
    msd: str | None = None # "subst:sg:nom:f"

    @classmethod
    def from_xml(cls, xml_token: etree._Element):
        return cls(
            orth=xml_token.text,
            lemma=xml_token.attrib['base'],
            pos=xml_token.attrib['ctag'],
            id=xml_token.attrib['id'],
            msd=xml_token.attrib['msd'],
            last_in_par=xml_token.get('lastInPar') == 'true',
            last_in_sent=xml_token.get('lastInSent') == 'true',
            has_nps=xml_token.get('hasNps') == 'true',
        )