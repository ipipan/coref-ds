from dataclasses import dataclass


@dataclass
class Segment:
    orth: str
    lemma: str
    has_nps: bool
    last_in_sent: bool | None = None
    last_in_par: bool | None = None
    pos: str | None = None
    number: str | None = None
    gender: str | None = None
    person: str | None = None
    id: str | None = None
    is_semantic_head: bool | None = None


@dataclass
class Mention:
    cluster_id: int
    mention_id: int
    span_start: int
    span_end: int
    head: str | None = None


class Text:
    def __init__(
        self,
        text_id: int | str,
        segments: list[str],
        segments_meta: list[Segment] | None = None,
        clusters: list[list[int]] | None = None,
        corpus_name: str | None = None,
    ):
        self.text_id = text_id
        self.segments = segments
        self.clusters = clusters if clusters else []
        self.segments_meta = segments_meta

    @property
    def clusters_str(self):
        clusters_str = []
        for cluster in self.clusters:
            cluster_str = []
            for span in cluster:
                start, *end = span
                end = end[0] if end else start
                cluster_str.append(tuple(self.segments[start : end + 1]))
            clusters_str.append(tuple(cluster_str))

        return tuple(clusters_str)

    def print_clusters(self):
        for cluster in self.clusters_str:
            for mention in cluster:
                print(' '.join(mention))
            print()
