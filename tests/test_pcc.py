import unittest
import tempfile
from pathlib import Path

from dotenv import dotenv_values
from coref_ds.tei.layers.coreference import CoreferenceLayer
from coref_ds.tei.layers.mention import MentionLayer
from coref_ds.tei.mention import Mention
from coref_ds.tei.layers.morphosyntax import MorphosyntaxLayer
from coref_ds.tei.layers.segmentation import SegmentationLayer
from coref_ds.tei.pcc import PCCStructureLayer
from coref_ds.utils import count_mentions

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
            Path(local_config['PCC_ROOT']) / 'train' / '38b',
        )
        clusters = tei_doc.text.clusters
        self.assertEqual(len(clusters), 77)
        all_mentions = set()
        for men in tei_doc.text.mentions:
            print(men.head, men.text)
            all_mentions.add(men.text)
        self.assertTrue('uczestników zajęć z informatyki' in all_mentions)
        self.assertEqual(len(all_mentions), len(set([men.text for men in tei_doc.text.mentions])))
        self.assertEqual(len(tei_doc.text.mentions), 93)

    def test_override_mentions(self):
        tei_doc = TEIDocument(
            Path(local_config['PCC_ROOT']) / 'train' / '38b',
        )
        clusters = tei_doc.text.clusters
        print(tei_doc.text.segments_meta)
        self.assertEqual(len(clusters), 77)
        tei_doc.layers['mentions'].remove_mentions()
        no_clusters = tei_doc.text.clusters
        self.assertEqual(len(no_clusters), 0)
        self.assertEqual(count_mentions(tei_doc), 0)
        ind = 0
        max_mentions = 20
        print('test')
        for cluster in clusters:
            for start, end in cluster:
                if ind == max_mentions:
                    break
                segments = tei_doc.text.segments[start:(end+1)]
                print(segments)
                tei_doc.layers['mentions'].add_mention(
                    Mention(
                        id=f"mention_{ind}",
                        text=' '.join(segments),
                        segments=segments,
                        span_start=start,
                        span_end=end,
                        lemmatized_text=None,
                        head_orth=None,
                        head=None,
                        cluster_id=None,
                    ),
                    tei_doc.text.segments_meta
                )
                ind += 1
        
        self.assertLessEqual(count_mentions(tei_doc), max_mentions)
        with tempfile.TemporaryDirectory() as tmpdirname:
            test_path = Path(tmpdirname).parent / 'test_override_mentions'
            tei_doc.to_file(test_path)
            tei_doc2 = TEIDocument(test_path)
            self.assertLessEqual(count_mentions(tei_doc2), max_mentions)
            print(list(tei_doc2.layers['mentions'].mention_nodes()))

        

