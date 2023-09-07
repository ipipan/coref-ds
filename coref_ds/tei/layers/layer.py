from abc import ABC, abstractmethod
from pathlib import Path
import gzip
import logging

from lxml import etree

logger = logging.getLogger(__name__)


class FileHandler:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        if self.path.suffix == ".gz":
            self.file = gzip.open(self.path, 'wb')
        else:
            self.file = self.path.open('wb')
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()


class XMLLayer:
    def __init__(self, file_path, namespace: dict):
        self.file_path = file_path
        self.root = None
        self.ns_map = namespace
        self._load()

    def _load(self):
        try:
            self.root = etree.parse(self.file_path).getroot()
        except etree.XMLSyntaxError as e:
            logger.error(f"Error while parsing {self.file_path}: {e}")
            self.root = None

    def to_file(self, file_dir: Path):
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / self.file_path.name
        with FileHandler(file_path) as f:
            f.write(etree.tostring(self.root, pretty_print=True, encoding="utf-8"))
        return file_path

    @abstractmethod
    def parse_layer(self):
        pass

    @abstractmethod
    def filter_by_sample_ids(self, sample_ids):
        pass
