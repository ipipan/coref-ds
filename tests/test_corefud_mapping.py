import unittest
import tempfile
from pathlib import Path
from coref_ds.corefud.utils import corefud_name_mapper

from dotenv import dotenv_values
from coref_ds.tei.layers.coreference import CoreferenceLayer
from coref_ds.tei.layers.mention import MentionLayer
from coref_ds.tei.mention import Mention
from coref_ds.tei.layers.morphosyntax import MorphosyntaxLayer
from coref_ds.tei.layers.segmentation import SegmentationLayer
from coref_ds.tei.pcc import PCCStructureLayer
from coref_ds.utils import count_mentions
from coref_ds.corefud.corefud_doc import CorefUDDoc

local_config = dotenv_values(".env")

corefud = Path(local_config["COREFUD_ROOT"])
pcc = corefud / 'CorefUD_Polish-PCC' / 'pl_pcc-corefud-dev0.conllu'


from coref_ds.tei.tei_doc import TEIDocument

layers_mapping = {
    'text_structure': (PCCStructureLayer, 'text'),
    'coreference': (CoreferenceLayer, 'ann_coreference'),
    'groups': (None, 'ann_groups'),
    'mentions': (MentionLayer, 'ann_mentions'),
    'morphosyntax': (MorphosyntaxLayer, 'ann_morphosyntax'),
    'named_entities': (None, 'ann_named'),
    'segmentation': (SegmentationLayer, 'ann_segmentation'),
    'senses': (None, 'ann_senses'),
}



def print_as_aligned(udapi_doc, text):
    l1, l2 = [], []
    for cluster in text.clusters_str:
        l1.append([' '.join(mention) for mention in cluster])
    for entity in udapi_doc.coref_entities:
        l2.append([' '.join([str(w.form) for w in m.words]) for m in entity.mentions])
    
    for c in sorted(l1):
        print(c)
    print('corefud')
    for c in sorted(l2):
        print(c)

def count_clusters(udapi_doc):
    return len(udapi_doc.coref_entities)


class TestCorefUDMapping(unittest.TestCase):
    def test_map_clusters(self):
        tei_texts = [
            TEIDocument(Path(local_config['PCC_ROOT']) / 'dev0' / '36e').text,
            TEIDocument(Path(local_config['PCC_ROOT']) / 'dev0' / '66b').text,
            TEIDocument(Path(local_config['PCC_ROOT']) / 'dev0' / '2678').text, # cross-sentence mention
            TEIDocument(Path(local_config['PCC_ROOT']) / 'dev0' / '2653').text, # zero anaphora
        ]
        cluster_lens = [len(text.clusters) for text in tei_texts]
        with tempfile.NamedTemporaryFile() as f:
            new_path = Path(f.name)
            doc = CorefUDDoc(pcc)
            doc.remove_coref()
            doc.map_clusters(tei_texts, docname_mapper=corefud_name_mapper)
            doc.to_file(new_path)

            doc2 = CorefUDDoc(new_path)
            for udapi_doc, text in zip(doc2.udapi_docs, tei_texts):
                print('mentions', len(udapi_doc.coref_mentions), len(text.mentions))
                #self.assertEqual(len(udapi_doc.coref_mentions), len(text.mentions))
                print_as_aligned(udapi_doc, text)

            for doc, clusters_number in zip(doc2.udapi_docs, cluster_lens): # assume order is the same
                # self.assertEqual(len(doc.coref_entities), clusters_number)
                print('clusters', len(doc.coref_entities), clusters_number)

