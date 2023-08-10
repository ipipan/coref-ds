from collections import defaultdict
import regex
from coref_ds.tei.layers.layer import XMLLayer
from coref_ds.tei.utils import remove_if_no_children


class SegmentationLayer(XMLLayer):
    def parse_layer(self):
        paragraphs = self.root.xpath('//tei:p', namespaces=self.ns_map)
        sentences = self.root.xpath('//tei:s', namespaces=self.ns_map)
        segments = self.root.xpath('//tei:seg', namespaces=self.ns_map)

        return {
            'paragraphs': paragraphs,
            'sentences': sentences,
            'segments': segments,
        }

    @staticmethod
    def get_sample_id(segment):
        """<seg corresp="text.xml#string-range(txt_1.2-ab,137,3)" xml:id="segm_1.44-seg"/>"""
        # write a regex to catch the "txt_1.2-ab" from the line above

        corresp = segment.attrib['corresp']

        sample_id = regex.match(r'text.xml#string-range\((.+),\d+,\d+\)', corresp).group(1)
        return sample_id

    @property
    def segmentation_mapping(self):
        segments = self.parse_layer()['segments']
        mapping = defaultdict(list)
        for segment in segments:
            sample_id = self.get_sample_id(segment)
            segment_id = segment.attrib[f'{{{self.ns_map["xmlns"]}}}id']
            mapping[sample_id].append(segment_id)

        return mapping

    def filter_by_sample_ids(self, sample_ids):
        segments = self.parse_layer()['segments']
        for segment in segments:
            sample_id = self.get_sample_id(segment)
            if sample_id not in sample_ids:
                parent = segment.getparent()
                parent.remove(segment)
                remove_if_no_children(parent, levels=2)
