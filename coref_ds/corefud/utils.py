

from collections import Counter, defaultdict
from pathlib import Path
import logging

import udapi

from coref_ds.align import align, align_heads, get_alignment
from coref_ds.text import Segment
from coref_ds.text import Mention

def get_paragraph_counts(p: Path):
    with open(p, 'r') as f:
        doc_lines = f.readlines()

    sent_id_lines = filter(lambda x: x.startswith('# sent_id'), doc_lines)
    sent_id = [line.split('-')[-1].strip() for line in sent_id_lines] # extract sentence id e.g. wsj0002-001-p1s0
    paragraph_ids = [int(line.split('s')[0].strip('p')) for line in sent_id] # extract paragraph id

    return Counter(paragraph_ids)

def corefud_name_mapper(name: str) -> str:
    # # newdoc id = input_data/PCC-1.5-MMAX/very_short/36e_words.xml
    name = name.split('/')[-1]
    name = name.split('_')[0]
    return name


def prepare_alignment(text, udapi_words_str):
        alignment, alignment_back = get_alignment(text.segments, udapi_words_str)
        aligned_clusters, indices_mapping = align(
            udapi_words_str, text.segments, text.clusters, alignment=alignment
            )
        aligned_heads = align_heads(text.heads, indices_mapping, alignment=alignment)
        return aligned_clusters, aligned_heads


def get_sent_id(word):
    if word:
        return word.address().split('#')[0]
    else:
        return None


def add_mention(
        mention,
        coref_entity,
        udapi_words,
        udapi_words_str,
        aligned_heads,
        mentions_set=None
          ):
    if mentions_set is None:
        mentions_set = set()
    if mention in mentions_set:
        return  # skip duplication in different cluster
    
    start, end = mention
    words = udapi_words[start:end]
    men_head_ind = aligned_heads.get(mention)
    head = udapi_words[men_head_ind] if men_head_ind else None
    sentence_ids_seq = [get_sent_id(word) for word in words]
    sentence_ids = set(sentence_ids_seq)
    if len(sentence_ids) > 1: # cross-sentence mention to split
        for sentence_id in sentence_ids:
            return
            print('sentence_id', sentence_id)
            sub_words = [word for word in words if get_sent_id(word) == sentence_id]
            sub_head = head if get_sent_id(head) == sentence_id else None
            doc_mention = coref_entity.create_mention(
                head=sub_head,
                words=sub_words,
            )
            print('cross-sentence', ' '.join([w.form for w in sub_words]), sub_head)
    else:
        doc_mention = coref_entity.create_mention(
            head=head,
            words=words,
            )
    mentions_set.add(mention)     


def node_to_segment(node: udapi.core.node.Node, node_position_in_text: int = None) -> str:
    try:
        prev_node = node.prev_node
    except IndexError:
        prev_node = None
        has_nps = False
    except TypeError as e:
        logging.info(f"Error in node {node.form} {node.address()}")
        prev_node = None
        has_nps = False
    else:
        has_nps = prev_node.no_space_after if prev_node else False

    meta = Segment(
        orth=node.form,
        lemma=node.lemma,
        has_nps=has_nps,
        pos=node.upos,
        id=node.address(),
        deprel=node.deprel,
        index=node_position_in_text,
    )
    return meta

def clusters_from_doc(doc):
    address2ind = {
        node.address():ind for ind, node in enumerate(doc.nodes_and_empty)
    }
    mentions = []
    clusters = defaultdict(list)
    for ent in doc.coref_entities:
        eid = ent.eid
        for men_ind, men in enumerate(ent.mentions):
            words = list(men.words)
            start_ind = address2ind[words[0].address()]
            end_ind = address2ind[words[-1].address()]
            clusters[ent.eid].append(
                (start_ind, end_ind)
            )
            mentions.append(
                Mention(
                    id=f"{eid}_{men_ind}",
                    text=' '.join([w.form for w in words]),
                    lemmatized_text=' '.join([w.lemma for w in words]),
                    segments=[node_to_segment(n, address2ind[men.head.address()]) for n in words],
                    span_start=start_ind,
                    span_end=end_ind,
                    head=address2ind[men.head.address()],
                    head_orth=men.head.form,
                )
            )

    return {
        'clusters': tuple(clusters.values()),
        'mentions': mentions
    }