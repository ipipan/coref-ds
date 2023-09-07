from dataclasses import dataclass

from lxml import etree

from coref_ds.text import Mention as MentionSchema


@dataclass
class Mention(MentionSchema):
    @classmethod
    def from_xml(xml):
        pass

    @staticmethod
    def morph_id(id: str):
        return f"ann_morphosyntax.xml#{id}"

    def to_xml(self, XML_NS, segment_nodes):
        seg = etree.Element('seg')
        seg.attrib[etree.QName(XML_NS, 'id')] = self.id
        fs = etree.SubElement(seg, 'fs', type='mention')
        head_ind = self.head if self.head else self.span_start
        f = etree.SubElement(fs, 'f', name='semh', fVal=self.morph_id(segment_nodes[head_ind].id))
        for ind in range(self.span_start, self.span_end + 1):
            morph_id = self.morph_id(segment_nodes[ind].id)
            ptr = etree.SubElement(seg, 'ptr', target=morph_id)
        return seg
