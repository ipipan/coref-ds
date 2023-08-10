import unittest
from pathlib import Path

from dotenv import dotenv_values

local_config = dotenv_values(".env")

from coref_ds.mmax.mmax_doc import MmaxDoc

class TestMmax(unittest.TestCase):
    def test_load(self):
        doc = MmaxDoc.from_file(Path(str(local_config['NKJP_MMAX_ROOT'])) / '0_anotowane' /'030-2-000000012.mmax')
        print(doc.doc_id)
        self.assertEqual(doc.text.segments[-2], 'teatr')
        self.assertEqual(len(doc.text.segments), 89)
        self.assertEqual(doc.text.segments_meta[-1].pos, 'interp')
        self.assertEqual(doc.text.segments_meta[-2].lemma, 'teatr')
        # print(list(doc.text.clusters[0])[0])
        # print(doc.text.print_clusters())
        all_mentions = set(mention for cluster in doc.text.clusters_str for mention in cluster)
        self.assertTrue(('ja', ',', 'który', 'śpię', ',', 'kiedy', 'otello', 'morduje', 'desdemonę') in all_mentions)

    def test_write(self):
        doc = MmaxDoc.from_file(Path(str(local_config['NKJP_MMAX_ROOT'])) / '0_anotowane' /'030-2-000000012.mmax')
        doc.to_file(Path('/tmp/'))
        doc2 = MmaxDoc.from_file(Path('/tmp/030-2-000000012.mmax'))
        self.assertEqual(doc.text.segments, doc2.text.segments)
        self.assertEqual(doc.text.clusters_str, doc2.text.clusters_str)

    def test_semantic_head_read(self):
        doc = MmaxDoc.from_file(Path(str(local_config['NKJP_MMAX_ROOT'])) / '0_anotowane' /'030-2-000000012.mmax')
        print(doc.doc_id)
        print(
            list([men.mention_head] for men in doc.mentions)
        )
