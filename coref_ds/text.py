from dataclasses import dataclass

@dataclass
class SegmentMeta:
    pass

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