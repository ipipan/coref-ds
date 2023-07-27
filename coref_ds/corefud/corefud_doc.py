from pathlib import Path
from collections import Counter
from abs import abstractmethod


import udapi
from tqdm import tqdm

from coref_ds.text import Text



class CorefUDDoc:
    def __init__(self, p: Path):
        self.doc_path = p
        self.corpus_name = p.parent.parent.name  # after preprocessing
        self.part = p.parent.name
        self.udapi_doc = None
        self.first_sentence_ind = 0
        self.first_paragraph_ind = 0
        self._clusters = None

    def parse_doc(self):
        if not self.udapi_doc:
            self.udapi_doc = udapi.Document(str(self.doc_path))

    @abstractmethod
    def get_sentence_ind(self, address: str) -> int:
        pass

    @abstractmethod
    def get_paragraph_ind(self, address: str) -> int:
        pass

    def get_index(self, address, first_sentence_ind = None, first_paragraph_ind = None):
        if first_sentence_ind is None:
            first_sentence_ind = self.first_sentence_ind

        paragraph_ind = 0
        if first_paragraph_ind is None:
            first_paragraph_ind = self.first_paragraph_ind

        paragraph_ind = self.get_paragraph_ind(address)
        sentence_ind = self.get_sentence_ind(address)

        return {
            'paragraph_ind': paragraph_ind - first_paragraph_ind,
            'sentence_ind': sentence_ind - first_sentence_ind,
        }
    
    @property
    def clusters(self) -> list[list[int]]:
        if self._clusters:
            return self._clusters
        else:
            clusters = []
            first_token = next(iter(self.udapi_doc.nodes_and_empty))
            self.first_sentence_ind, self.first_paragraph_ind = self.get_sentence_ind(first_token.address())

    @property
    def text(self) -> Text:
        pass

