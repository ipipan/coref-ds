import unittest
import tempfile
from pathlib import Path

from dotenv import dotenv_values

from coref_ds.corefud.corefud_doc import CorefUDDoc
from coref_ds.corefud.corefud_writer import write_corefud

local_config = dotenv_values(".env")

corefud = Path(local_config["COREFUD_ROOT"])
pcc_single_texts = Path(local_config["PCC_COREFUD_SINGLE_TEXTS"])
pcc = corefud / 'pl_pcc-corefud-test.conllu'
pcc_train = corefud / 'pl_pcc-corefud-train.conllu'

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


    def test_deprels(self):
        self.assertTrue(pcc.exists())
        # doc = CorefUDDoc(pcc)
        doc = CorefUDDoc(pcc_single_texts / 'train' / '3165.conllu')
        doc1 = doc.udapi_docs[0]
        doc.udapi_docs = [doc1]
        text = doc.text
        for cluster in text.clusters:
            for start, end in cluster:
                self.assertEqual(
                    start, text.segments_meta[start].get_token_index()
                )
                self.assertEqual(text.segments_meta[end].get_token_index(), end)
                print({
                    'segments indices': [text.segments_meta[start].get_token_index(), text.segments_meta[end].get_token_index()],
                    'cluster indices': [start, end],
                    'text': ' '.join(text.segments[start:(end+1)])
                })



    def test_write_corefud(self):
        paths = list(pcc_single_texts.glob('*/*.conllu'))[400:600]
        texts = []
        error_paths = []
        for path in paths:
            print(path)
            try:
                doc = CorefUDDoc(path)
                text = doc.text
                texts.append(text)
            except Exception as e:
                error_paths.append(path)
                raise e
        print(len(error_paths))
        write_corefud(texts, 'testing_corefud.conllu')


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

