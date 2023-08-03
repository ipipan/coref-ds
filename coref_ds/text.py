from dataclasses import dataclass

@dataclass
class SegmentMeta:
    orth: str
    lemma: str
    has_nps: bool
    last_in_sent: bool | None = None
    last_in_par: bool | None = None
    pos: str | None = None
    number: str| None = None
    gender: str| None = None
    person: str | None = None


class Text:
    def __init__(
        self,
        text_id: int | str,
        segments: list[str],
        segments_meta: list[SegmentMeta] | None = None,
        clusters: list[list[int]] | None = None,
        corpus_name: str | None = None,
    ):
        self.text_id = text_id
        self.segments = segments
        self.clusters = clusters if clusters else []
        self.segments_meta = segments_meta