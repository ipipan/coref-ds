from dataclasses import dataclass


@dataclass
class Mention:
    id: str
    text: str
    lemmatized_text: str
    segments: list
    span_start: int
    span_end: int
    head_orth: str
    head: str
    cluster_id: int

    @classmethod
    def from_xml(xml):
        pass

    def to_xml(self):
        pass
