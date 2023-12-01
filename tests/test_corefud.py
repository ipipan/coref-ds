import unittest
import tempfile
from pathlib import Path

from dotenv import dotenv_values

from coref_ds.corefud.corefud_doc import CorefUDDoc

local_config = dotenv_values(".env")

corefud = Path(local_config["COREFUD_ROOT"])
pcc_single_texts = Path(local_config["PCC_COREFUD_SINGLE_TEXTS"])
pcc = corefud / 'CorefUD_Polish-PCC' / 'pl_pcc-corefud-dev0.conllu'
pcc_train = corefud / 'CorefUD_Polish-PCC' / 'pl_pcc-corefud-train.conllu'

class TestCorefUD(unittest.TestCase):
    def test_empty_mentions(self):
        with tempfile.NamedTemporaryFile() as f:
            new_path = Path(f.name)
            self.assertTrue(pcc.exists())
            doc = CorefUDDoc(pcc)
            doc.remove_coref()
            doc.to_file(new_path)
            doc2 = CorefUDDoc(new_path)
            for udapi_doc in doc2.udapi_docs + doc.udapi_docs:
                self.assertEqual(len(udapi_doc.coref_entities), 0)


    def test_to_text(self):
        self.assertTrue(pcc.exists())
        doc = CorefUDDoc(pcc)
        doc1 = doc.udapi_docs[0]
        doc.udapi_docs = [doc1]
        text = doc.text
        print(doc.text.print_clusters())

    def test_all_texts(self):
        paths = list(pcc_single_texts.glob('*/*.conllu'))
        error_paths = []
        # doc = CorefUDDoc(pcc_train)
        # text = doc.text
        for path in paths:
            try:
                doc = CorefUDDoc(path)
                text = doc.text
            except Exception as e:
                error_paths.append(path)
                raise e

        self.assertEqual(len(paths), 1828)
        print(len(error_paths))

