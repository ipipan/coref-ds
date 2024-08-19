from collections import defaultdict
from pathlib import Path
import json
from dataclasses import dataclass
from datetime import datetime

import conllu
from conllu import TokenList

from coref_ds.text import Text
from coref_ds.text import Mention
from coref_ds.text import Segment

with open('pcc_structure_reversed.json', 'r') as json_file:
    pcc_structure_reversed = json.load(json_file)


def gen_full_text_id(text: Text):
    text_type = pcc_structure_reversed[text.text_id]
    return f"input_data/PCC-1.5-MMAX/{text_type}/{text.text_id}_words.xml"


def get_entity_id(m: Mention, text_id: str):
    return f"e{text_id}{m.cluster_id}1"


def gen_entity_markup_introduction(mention: Mention, text_id: str):
    # get in-mentions position of mention head
    mention_orths = [s.orth for s in mention.segments]
    head_position = mention_orths.index(mention.head_orth) + 1

    return f"{get_entity_id(mention, text_id)}--{head_position}-id:markable_{mention.id.removeprefix('mention_')},mention_head:{mention.head_orth}"


def get_sentence_text(sentence: list[Segment]):
    text = []
    for seg in sentence:
        if not seg.has_nps:
            text.append(' ')

        text.append(seg.orth)

    return ''.join(text)


def get_indices_to_mention_mapping(text: Text):
    index_to_mention_start = defaultdict(list)
    index_to_mention_end = defaultdict(list)
    span_to_mention = {}
    mention_id = 0
    
    for m in text.mentions:
        span_to_mention[(m.span_start, m.span_end)] = m

        # filter multi-sentence mentions @TODO improve this
        for s in m.segments:
            if s.last_in_sent:
                span_to_mention[(m.span_start, m.span_end)] = None
                break

    for cluster_id, cluster in enumerate(text.clusters):
        for m_span in cluster:
            if span_to_mention[m_span] is not None:
                m = span_to_mention[m_span]
                m.cluster_id = cluster_id
                m.mention_id = mention_id
                mention_id += 1

                index_to_mention_start[m.span_start].append(m)
                index_to_mention_end[m.span_end].append(m)

    text.index_to_mention_start = index_to_mention_start
    text.index_to_mention_end = index_to_mention_end

    return text


def gen_corefud_for_token(seg: Segment, text: Text, sentence: list[Segment]):
    entities = []
    seg_ind = seg.get_token_index()

    mentions_starting_at_seg = text.index_to_mention_start[seg_ind]
    mentions_ending_at_seg = text.index_to_mention_end[seg_ind]
    singletons_ids_at_seg = set([m.id for m in mentions_starting_at_seg]) & set([
        m.id for m in mentions_ending_at_seg])
    singletons_at_seg = [
        m for m in mentions_starting_at_seg if m.id in singletons_ids_at_seg]

    mentions_starting_at_seg = list(
        filter(lambda m: m.id not in singletons_ids_at_seg, mentions_starting_at_seg))
    mentions_ending_at_seg = list(
        filter(lambda m: m.id not in singletons_ids_at_seg, mentions_ending_at_seg))

    mentions_starting_at_seg.sort(key=lambda m: m.span_end)
    mentions_ending_at_seg.sort(key=lambda m: m.span_start)

    for m in mentions_ending_at_seg:
        entities.append(
            f"{get_entity_id(m, text.text_id)})"
        )
    for m in mentions_starting_at_seg:
        entities.append(
            f"({gen_entity_markup_introduction(m, text.text_id)}"
        )
    for m in singletons_at_seg:
        entities.append(
            f"({gen_entity_markup_introduction(m, text.text_id)})"
        )

    if entities:
        return 'Entity=' + ''.join(entities)
    else:
        return '_'


def text_to_corefud(text: Text) -> list[TokenList]:
    text = get_indices_to_mention_mapping(text)
    sentences = []
    curr_sentence = None

    for seg in text.segments_meta:
        if not curr_sentence:
            curr_sentence = [seg]
        else:
            curr_sentence.append(seg)

        if seg.last_in_sent:
            sentences.append(curr_sentence)
            curr_sentence = None
    if curr_sentence:
        sentences.append(curr_sentence)
        curr_sentence = None
    # for every sentence:
        #  - sentence_id
        # - full sentence text (spaced)
    conllu_sents = []
    for sent_ind, sentence in enumerate(sentences):
        sent_id = sent_ind + 1
        data = []
        for seg_pos, seg in enumerate(sentence):
            # this mapping should be moved into Segment class

            misc = gen_corefud_for_token(seg, text, sentence)
            data.append({
                "id": seg_pos,
                "form": seg.orth,
                "lemma": seg.lemma,
                "upostag": '_',
                "xpostag": seg.pos,
                "feats": '_',  # update from gender, number, person
                "head": seg.dep_head if seg.dep_head else '_',
                "deprel": seg.deprel.lower() if seg.deprel else '_',
                "deps": '_',
                "misc": misc,
            })
        conllu_sent = conllu.TokenList(
            data, metadata={"sent_id": sent_id, "text": get_sentence_text(sentence)})
        conllu_sents.append(conllu_sent)

    return conllu_sents


def texts_to_corefud(texts: list[Text]):
    entity_metadata = "global.Entity = eid-etype-head-other"
    lines = []

    for text in texts:
        text_sents = text_to_corefud(text)
        lines.extend([
            f"# newdoc id = {gen_full_text_id(text)}",
            "\n",
            f"# {entity_metadata}"
        ])
        for token_list in text_sents:
            lines.append(token_list.serialize())

    return ''.join(lines) + "\n"


def write_corefud(texts: list[Text], p: Path):
    with open(p, "w") as f:
        f.write(texts_to_corefud(texts))
