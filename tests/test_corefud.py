import unittest
import tempfile
from pathlib import Path

from dotenv import dotenv_values

from coref_ds.corefud.corefud_doc import CorefUDDoc

local_config = dotenv_values(".env")

corefud = Path(local_config["COREFUD_ROOT"])
pcc = corefud / 'CorefUD_Polish-PCC' / 'pl_pcc-corefud-dev0.conllu'

class TestCorefUD(unittest.TestCase):
    def test_empty_mentions(self):
        with tempfile.NamedTemporaryFile() as f:
            new_path = Path(f.name)
            doc = CorefUDDoc(pcc)
            doc.remove_coref()
            doc.to_file(new_path)
            doc2 = CorefUDDoc(new_path)
            for doc in doc2.udapi_docs:
                self.assertEqual(len(doc.coref_entities), 0)

