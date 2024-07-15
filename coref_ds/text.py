from dataclasses import dataclass, field
import copy


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
    id: str
    text: str
    segments: list
    span_start: int
    span_end: int
    lemmatized_text: str | None = None
    head_orth: str | None = None
    head: int | None = None
    cluster_id: int | None = None


@dataclass
class Text:
    text_id: str 
    segments: list[str]
    clusters: list[list[tuple[int, int]]] = field(default_factory=list)
    segments_meta: list[Segment] = field(default_factory=list)

    @property
    def clusters_str(self):
        clusters_str = []
        for cluster in self.clusters:
            cluster_str = []
            for span in cluster:
                start, *end = span
                end = end[0] if end else start
                cluster_str.append(self.segments[start : end + 1])
            clusters_str.append(tuple(cluster_str))

        return tuple(clusters_str)

    def print_clusters(self):
        for cluster in self.clusters_str:
            for mention in cluster:
                print(' '.join(mention))
            print()
    
    @property
    def heads(self):
        if not hasattr(self, 'mentions') or not hasattr(self, 'indices_to_mentions'):
            raise AttributeError()
        
        heads = {}
        for cluster in self.clusters:
            cluster_heads = []
            for mention_span in cluster:
                heads[mention_span] = self.indices_to_mentions[mention_span].head

        return heads

    @staticmethod
    def get_subtexts(text, split_key='last_in_sent'):
        subtexts = []
        curr_subtext = copy.deepcopy(text)
        curr_segments = []
        curr_segments_meta = []
        curr_start_ind = 0

        name_dict = {'last_in_sent': 's', 'last_in_par': 'p'}

        for ind, segment in enumerate(text.segments):
            curr_segments.append(segment)
            curr_segments_meta.append(text.segments_meta[ind])

            if getattr(text.segments_meta[ind], split_key, None):
                curr_subtext.segments = curr_segments
                curr_subtext.segments_meta = curr_segments_meta
                curr_subtext.text_id += f"_{name_dict[split_key]}_{len(subtexts)}"
                Text.trim_indexes_after_split(curr_subtext, curr_start_ind, ind)
                subtexts.append(curr_subtext)
                curr_subtext = copy.deepcopy(text)
                curr_segments = []
                curr_segments_meta = []
                curr_start_ind = ind + 1

        return subtexts

    @staticmethod
    def trim_indexes_after_split(text, text_start_ind, text_end_ind):
        text_range = range(text_start_ind, text_end_ind)
        new_clusters = []
        for cluster_ind, cluster in enumerate(text.clusters):
            new_spans = []
            for span_start, span_end in cluster:
                if span_start not in text_range or span_end not in text_range:
                    continue
                else:
                    new_span = span_start - text_start_ind, span_end - text_start_ind
                    new_spans.append(new_span)

            if new_spans:
                new_clusters.append(new_spans)
        text.clusters = new_clusters
        return text
    

    def __repr__(self):
        repr = []
        return ''.join(
            [f'\n\n --- Cluster {ind} --- \n' + ' | '.join(cluster) for ind, cluster in enumerate(self.clusters_str)]
        ).strip()