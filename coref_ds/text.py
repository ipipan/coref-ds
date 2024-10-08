from collections import defaultdict
from dataclasses import dataclass, field
import copy
import re
import logging

from coref_ds.utils import any_segment_is_head, find_incremental_subsequences


@dataclass
class Segment:
    orth: str
    lemma: str
    has_nps: bool
    index: int
    last_in_sent: bool | None = None
    last_in_par: bool | None = None
    pos: str | None = None
    number: str | None = None
    gender: str | None = None
    person: str | None = None
    deprel: str | None = None
    dep_head: int | None = None
    id: str | None = None
    is_semantic_head: bool | None = None


    def get_token_index(self):
        """
        return segment (token) position in text
        """
        return self.index

    def is_orth_equal(self, orth):
        return self.orth == orth


@dataclass
class Mention:
    id: str
    text: str
    segments: list
    span_start: int
    span_end: int
    lemmatized_text: str | None = None
    head_orth: str | None = None
    head: int | None = None  # index of the head token in text
    cluster_id: int | None = None
    is_continuous: bool = True
    mention_segment_to_text_index: list | None = None

    def __post_init__(self):
        incremental_subsequences = find_incremental_subsequences(self.segments)
        assert len(incremental_subsequences) > 0
        if len(incremental_subsequences) == 1:
            self.is_continuous = True
        else:
            self.is_continuous = False
            self.submentions = incremental_subsequences
            self.maximal_continuous_mention = self.get_max_cont_mention()
            self.span_start, self.span_end = self.maximal_continuous_mention[0].get_token_index(), \
                self.maximal_continuous_mention[-1].get_token_index()
            
            self.full_segments = self.segments
            self.segments = self.maximal_continuous_mention # that's too tricky

    def get_max_cont_mention(self):
        # maximal continous mention
        if self.submentions:
            try:
                max_continuous_submention = list(filter(
                    lambda x: any_segment_is_head(
                        x, self.head_orth, self.head), self.submentions
                ))[0]
                return max_continuous_submention
            except IndexError:
                # head outside of mention? It could happen for dependency tree determined heads.
                # maybe this should be in a more appropriate data structure
                logging.exception(f"""
                                 number of submentions: {len(self.submentions)}
                                 mention_head: {self.head} {self.head_orth}
                                 segments: {[s.orth for s in self.segments]}
                                 submentions: {self.submentions}
                                 """)
                print("IndexError")
                return sorted(self.submentions, key=len)[-1]

        return []

    def __iter__(self, include_noncontinuous=False):
        yield self.get_mention_span(include_noncontinuous)

    def get_mention_span(self, include_noncontinuous=False):
        if self.is_continuous or not include_noncontinuous:
            return self.span_start, self.span_end
        elif include_noncontinuous:
            return [
                (submention[0].get_token_index(), submention[-1].get_token_index()) for submention in self.submentions
            ]


@dataclass
class Text:
    text_id: str
    segments: list[str]
    clusters: list[list[tuple[int, int]]] = field(default_factory=list)
    segments_meta: list[Segment] = field(default_factory=list)
    mentions: list[Mention] | None = None

    @property
    def clusters_str(self):
        clusters_str = []
        for cluster in self.clusters:
            cluster_str = []
            for span in cluster:
                start, *end = span
                end = end[0] if end else start
                cluster_str.append(self.segments[start: end + 1])
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
                curr_subtext.text_id += f"_{
                    name_dict[split_key]}_{len(subtexts)}"
                Text.trim_indexes_after_split(
                    curr_subtext, curr_start_ind, ind)
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

        for ind, cluster in enumerate(self.clusters_str):
            repr.append(f'\n\n --- Cluster {ind} --- \n')

            for mention in cluster:
                repr.append(' '.join(mention))
                repr.append(' | ')

        return ''.join(repr)

    def find_agglutinants(self):
        c_tags = ['interp', 'ign']
        agglutinative_phrases = set()
        for ind, seg in enumerate(self.segments_meta[:-1]):
            next_token_global_ind_diff = 1
            next_token_ind = ind + next_token_global_ind_diff
            if (
                seg.pos not in c_tags and
                self.segments_meta[next_token_ind].pos not in c_tags and
                (self.segments_meta[next_token_ind].has_nps is True or
                 self.segments_meta[next_token_ind].orth in {'eś', 'ś', 'śmy', 'ście', 'by', 'M', 'm', 'em', 'ń', 'by', 'BY', 'aś'}
                )
            ):
                agglutinative_phrases.add(next_token_ind)

        return agglutinative_phrases

    def merge_agglutinative_mentions(self, verbose=False):
        agg_indices = self.find_agglutinants()
        merged_mentions = []
        new_clusters_dict = defaultdict(list)
        for mention in self.mentions:
            first_segment = mention.segments[0]
            if first_segment.index in agg_indices:
                to_print = [mention.text]
                new_start_ind = first_segment.index - 1
                mention.segments[0].has_nps = True
                seg_to_add = self.segments_meta[new_start_ind]
                mention.segments.insert(0, seg_to_add)
                mention.span_start = new_start_ind
                mention.text = seg_to_add.orth + ' ' + mention.text
                mention.lemmatized_text = seg_to_add.lemma + ' ' + mention.lemmatized_text
                mention.__post_init__()
                merged_mentions.append(mention)
                to_print.append(mention.text.replace(" ", ""))
                if verbose:
                    print(self.text_id, ' '.join(to_print))

            new_clusters_dict[mention.cluster_id].append((mention.span_start, mention.span_end))

        self.clusters = tuple(new_clusters_dict.values())
        return merged_mentions
