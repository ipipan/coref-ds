from coref_ds.tei.layers.layer import XMLLayer
from coref_ds.tei.utils import remove_if_no_children


class NKJPStructureLayer(XMLLayer):

    def parse_sample_metadata(self, sample_ab):
        #  <ab n="p82in90of:PWN:010-2-000000001" xml:id="txt_2.1-ab"
        name_parts = sample_ab.attrib['n'].split(':')
        sample_id = sample_ab.attrib[f'{{{self.ns_map["xmlns"]}}}id']

        if len(name_parts) >= 2:
            text_name = name_parts[-1]
            source_name = ':'.join(name_parts[-2:0])
            text_part = name_parts[0].split('in')[-1]
            text_paragraph = int(name_parts[0].split('in')[0].strip('p'))

            return {
                'text_name': text_name,
                'source_name': source_name,
                'text_part': text_part,
                'sample_id': sample_id,
                'text_paragraph': text_paragraph,
            }
        elif len(name_parts) == 1:
            name = name_parts[0]
            return {
                'text_name': name,
                'source_name': name,
                'text_part': name,
                'sample_id': 'txt_1',
            }
        else:
            print(name_parts, sample_ab, self.file_path)
            raise ValueError('Wrong name parts')

    def parse_layer(self):
        divs = self.root.xpath('//tei:div', namespaces=self.ns_map)
        div_samples = []
        for div in divs:
            samples = div.xpath('.//tei:ab', namespaces=self.ns_map)
            div_samples.append(samples)
        return {
            'div_samples': div_samples,
            'divs': divs,
        }

    @property
    def continuous_excerpts(self):
        structure = self.parse_layer()
        parsed_samples = []
        for div_samples in structure['div_samples']:
            parsed_samples.append(
                [self.parse_sample_metadata(sample) for sample in div_samples]
            )

        return parsed_samples

    def filter_by_sample_ids(self, sample_ids):
        structure = self.parse_layer()

        for div, div_samples in zip(structure['divs'], structure['div_samples']):
            for sample in div_samples:
                sample_id = self.parse_sample_metadata(sample)['sample_id']
                if sample_id not in sample_ids:
                    div.remove(sample)
            remove_if_no_children(div)
