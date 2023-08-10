import unittest
from pathlib import Path

from dotenv import dotenv_values
from coref_ds.tei.layers.coreference import CoreferenceLayer
from coref_ds.tei.layers.mention import MentionLayer
from coref_ds.tei.layers.morphosyntax import MorphosyntaxLayer
from coref_ds.tei.layers.segmentation import SegmentationLayer
from coref_ds.tei.pcc import PCCStructureLayer

local_config = dotenv_values(".env")

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


class TestPCC(unittest.TestCase):
    def test_load(self):
        tei_doc = TEIDocument(
            Path(local_config['PCC_ROOT']) / '38b',
        )
        clusters = tei_doc.text.clusters
        self.assertEqual(len(clusters), 77)
        all_mentions = set()
        for men in tei_doc.text.mentions:
            print(men.head.orth, men.text)
            all_mentions.add(men.text)
        self.assertTrue('uczestników zajęć z informatyki' in all_mentions)
        self.assertEqual(len(all_mentions), len(set([men.text for men in tei_doc.text.mentions])))
        self.assertEqual(len(tei_doc.text.mentions), 93)

