from dataclasses import dataclass

from lxml import etree

from coref_ds.mmax.attributes import MARKABLE_ATTRIBUTES

@dataclass
class Markable:
    id: str
    span: str
    indirect_other_facet: str
    excluding_ios_facet: str
    excluding_negation_facet: str
    indirect_bound: str
    supporting_metareference: str
    supporting_comparison_facet: str
    indirect_aggregation: str
    indirect_aggregation_facet: str
    supporting_comparison: str
    excluding_other_facet: str
    indirect_compositon: str
    excluding_contrast: str
    excluding_other: str
    indirect_compositon_facet: str
    indirect_bound_facet: str
    indirect_other: str
    mention_group: str
    excluding_polysemy_facet: str
    excluding_negation: str
    supporting_metareference_facet: str
    mention_head: str
    mention_type: str
    near_identity_facet: str
    supporting_other: str
    mmax_level: str
    near_identity: str
    supporting_predicative: str
    excluding_polysemy: str
    supporting_predicative_facet: str
    excluding_contrast_facet: str
    excluding_ios: str
    supporting_other_facet: str

    @classmethod
    def from_xml(cls, xml_markable: etree._Element):
        return cls(
            **{k: xml_markable.attrib[k] if xml_markable.attrib[k] else MARKABLE_ATTRIBUTES[k]
               for k in MARKABLE_ATTRIBUTES}
        )

    def get_span(self):
        start, *end = self.span.split('..')
        end = end[0] if end else start
        try:
            start, end = (int(el.split('_')[-1]) for el in (start, end))  # "word_0" -> 0
        except ValueError as e:
            print(f'Error while parsing span: {self.span}')
            return None
        else:
            return start, end