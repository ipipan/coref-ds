from dataclasses import dataclass
from io import StringIO

from lxml import etree

from coref_ds.mmax.attributes import MARKABLE_ATTRIBUTES
from coref_ds.utils import add_element

@dataclass
class Markable:
    id: str  # markable_10
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
    span_start: int | None = None
    span_end: int | None = None

    @staticmethod
    def gen_span_attr(span_start: int, span_end: int):
        span_start = f'word_{str(span_start)}'
        span_end = f'word_{str(span_end-1)}'
        return f'{span_start}..{span_end}'

    @classmethod
    def from_xml(cls, xml_markable: etree._Element):
        return cls(
            **{k: xml_markable.attrib[k] if xml_markable.attrib[k] else MARKABLE_ATTRIBUTES[k]
               for k in MARKABLE_ATTRIBUTES}
        )

    def get_span(self):
        start, *end = self.span.split('..') 
        end = end[0] if end else start # @TODO non-continuous spans
        try:
            start, end = (int(el.split('_')[-1]) for el in (start, end))  # 'word_0' -> 0
        except ValueError as e:
            print(f'Error while parsing span: {self.span}')
            return None
        else:
            return start, end


    def to_xml(self, mentions_tree: etree._Element):
        if self.span_start and self.span_end:
            span = self.gen_span_attr(self.span_start, self.span_end)
        else:
            span = self.span  # @TODO get span from span string in the object
        add_element(
            mentions_tree,
            'markable',
            attributes={
                'id': self.id,
                'span': span,
                'indirect_other_facet': 'none',
                'excluding_ios_facet': 'none',
                'excluding_negation_facet': 'none',
                'indirect_bound': 'none',
                'supporting_metareference': 'none',
                'supporting_comparison_facet': 'none',
                'indirect_aggregation': 'empty',
                'indirect_aggregation_facet': 'none',
                'supporting_comparison': 'none',
                'excluding_other_facet': 'none',
                'indirect_compositon':'empty',
                'excluding_contrast':'empty',
                'excluding_other':'empty',
                'indirect_compositon_facet':'none',
                'indirect_bound_facet':'none',
                'indirect_other':'empty',
                'mention_group': self.mention_group,
                'excluding_polysemy_facet':'none',
                'excluding_negation':'empty',
                'supporting_metareference_facet':'none',
                'mention_head': self.mention_head if self.mention_head else '',
                'mention_type':'system',
                'near_identity_facet':'none',
                'supporting_other':'empty',
                'mmax_level':'mention',
                'near_identity':'empty',
                'supporting_predicative':'empty',
                'excluding_polysemy':'empty',
                'supporting_predicative_facet':'none',
                'excluding_contrast_facet':'none',
                'excluding_ios':'empty',
                'supporting_other_facet':'none'
            }
        )

def gen_mentions_structure():
    schema = """<?xml version="1.0"?>
        <!DOCTYPE markables SYSTEM "markables.dtd">
        <markables xmlns="www.eml.org/NameSpaces/mention">
        </markables>
    """
    ccl = etree.parse(StringIO(schema))

    return ccl
