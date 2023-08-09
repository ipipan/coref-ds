from dataclasses import dataclass
from io import StringIO

from lxml import etree

from coref_ds.text import Segment
from coref_ds.utils import add_element

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
    
    def to_xml(self, words_tree, segment_id):
        annotation_dict = {
                'base': self.lemma,
                'ctag': self.pos.split(':')[0],
                'id': f"word_{str(segment_id)}",
                'msd': self.pos
            }
        for name_in, name_out in [
            ('has_nps', 'has_nps'),
            ('last_in_sent', 'last_in_sent'),
            ('last_in_par', 'last_in_par')
        ]:
            if getattr(self, name_in):
                annotation_dict[name_out] = 'true'

        add_element(
            words_tree,
            'word',
            self.orth,
            annotation_dict
        )
    

def gen_words_structure():
    schema = """<?xml version='1.0'?>
        <!DOCTYPE words SYSTEM "words.dtd">
        <words>
        </words>
    """
    ccl = etree.parse(StringIO(schema))

    return ccl
