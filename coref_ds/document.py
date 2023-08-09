from abc import abstractmethod
from pathlib import Path


from coref_ds.text import Text


class CorefDoc:
    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def from_file(cls, p: Path):
        pass

    @abstractmethod
    def to_file(self, p: Path):
        pass

    @staticmethod
    @abstractmethod
    def load_files(self, p: Path):
        pass

    @abstractmethod
    def parse_doc(self):
        pass

    @property
    @abstractmethod
    def text(self) -> Text:
        pass
