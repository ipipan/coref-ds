from coref_ds.tei.layers.layer import XMLLayer
from coref_ds.tei.utils import get_feature_val


class CoreferenceLayer(XMLLayer):
    def parse_layer(self):
        parts = self.root.xpath(".//tei:p", namespaces=self.ns_map)
        mention_clusters = []
        for par in parts:
            par_cluster = par.xpath(".//tei:seg", namespaces=self.ns_map)
            for cor in par_cluster:
                mention_clusters.append(cor)
        return mention_clusters

    def add_clusters_to_text(self, clusters, text, xml_ns='http://www.w3.org/XML/1998/namespace'):
        for cluster in clusters:
            idx = cluster.attrib[f'{{{xml_ns}}}id']

            coref_type = None
            dominant = None
            for f in cluster.xpath(".//tei:f", namespaces=self.ns_map):
                if f.attrib['name'] == 'type':
                    coref_type = get_feature_val(f)
                elif f.attrib['name'] == 'dominant':
                    dominant = get_feature_val(f)

            if coref_type == 'ident':
                for ptr in cluster.xpath(".//tei:ptr", namespaces=self.ns_map):
                    mnt_id = ptr.attrib['target'].split('#')[-1]
                    curr_mention = None
                    for mention in text.mentions:
                        if mention.id == mnt_id:
                            curr_mention = mention
                            break
                    if curr_mention:
                        curr_mention.cluster_id = idx
                        curr_mention.dominant = dominant
