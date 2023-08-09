import unittest
from pathlib import Path

from dotenv import dotenv_values

local_config = dotenv_values(".env")

from coref_ds.ccl.ccl_doc import CclDoc

class TestCcl(unittest.TestCase):
    def test_load(self):
        doc = CclDoc.from_file(Path(str(local_config['KPWR_ROOT'])) / '00100508.xml')
        print(doc.doc_id)
        self.assertEqual(str(doc.segments[-2]), 'osób')
        self.assertEqual(len(doc.segments), 26)
        self.assertEqual(doc.segments[-1].pos, 'interp')
        self.assertEqual(doc.segments[-2].lemma, 'osoba')
        self.assertEqual(doc.text.segments_meta[-1].pos, 'interp')
