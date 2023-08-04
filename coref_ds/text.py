from dataclasses import dataclass

@dataclass
class Segment:
    orth: str
    lemma: str
    has_nps: bool
    last_in_sent: bool | None = None
    last_in_par: bool | None = None
    pos: str | None = None
    number: str| None = None
    gender: str| None = None
    person: str | None = None
    id: str | None = None
    is_semantic_head: bool | None = None


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
                cluster_str.append(
                    tuple(self.segments[span[0] : span[1] + 1])
                    )
            clusters_str.append(cluster_str)

        return clusters_str
    
    def print_clusters(self):
        for cluster in self.clusters_str:
            for mention in cluster:
                print(' '.join(mention))
            print()