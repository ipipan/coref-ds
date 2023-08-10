from coref_ds.tei.layers.layer import XMLLayer


class PCCStructureLayer(XMLLayer):

    def parse_sample_metadata(self, sample):
        return {
            'text_name': sample.attrib[f'{{{self.ns_map["xmlns"]}}}id'],
        }

    def parse_layer(self):
        samples = self.root.xpath('//tei:p', namespaces=self.ns_map)
        return {
            'samples': samples,
            'divs': None,
        }