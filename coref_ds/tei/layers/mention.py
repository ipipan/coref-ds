import re

from lxml import etree

from coref_ds.tei.layers.layer import XMLLayer
from coref_ds.tei.mention import Mention
from coref_ds.tei.utils import get_feature_val, remove_if_no_children, to_text, word_to_ignore


class MentionLayer(XMLLayer):
    @staticmethod
    def get_mention(mention, mnt_id, segments, segments_ids, paragraph_id, sentence_id, ns_map):
        idx = mention.attrib[f'{{{ns_map["xmlns"]}}}id']

        mnt_segments = []
        for ptr in mention.xpath(".//tei:ptr", namespaces=ns_map):
            seg_id = ptr.attrib['target'].split('#')[-1]
            if not word_to_ignore(segments[seg_id]):
                mnt_segments.append(segments[seg_id])

        semh = None
        for f in mention.xpath(".//tei:f", namespaces=ns_map):
            if f.attrib['name'] == 'semh':
                semh_id = get_feature_val(f).split('#')[-1]
                semh = segments[semh_id]

        if len(mnt_segments) == 0:
            mnt_segments.append(semh)


        mention = Mention(
            id=idx,
            text=to_text(mnt_segments, 'orth'),
            lemmatized_text=to_text(mnt_segments, 'lemma'),
            segments=mnt_segments,
            span_start=segments_ids.index(mnt_segments[0].id),
            span_end=segments_ids.index(mnt_segments[-1].id),
            head_orth=semh.orth,
            head=semh,
            cluster_id=None,
        )

        return mention

    def mention_nodes(self):
        paragraphs = self.root.xpath("//tei:p", namespaces=self.ns_map)
        mnt_id = 0
        for par_id, par in enumerate(paragraphs):
            mention_nodes = par.xpath(".//tei:seg", namespaces=self.ns_map)
            for mnt in mention_nodes:
                yield mnt, mnt_id, par_id

    def parse_layer(self, segments, segments_ids):
        mentions = []
        for mnt, mnt_id, par_id in self.mention_nodes():
            mention = MentionLayer.get_mention(
                mnt, mnt_id, segments, segments_ids, par_id, sentence_id=None, ns_map=self.ns_map
            )
            mentions.append(mention)

        return mentions
    
    def remove_mentions(self):
        for mention, mnt_id, par_id in self.mention_nodes():
            parent = mention.getparent()
            parent.remove(mention)

    def add_mention(self, mention: Mention, segments):
        p_el = self.root.xpath("//tei:p", namespaces=self.ns_map)[0] # assumes there is only one <p/>
        comment = re.sub('-', ' ', mention.text)
        p_el.append(etree.Comment(comment))
        p_el.append(mention.to_xml(self.ns_map['xmlns'], segments))