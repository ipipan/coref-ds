import spacy_alignments


def align_mention(mention_inds, subtoken2token_indices, annotated_tokens=None):
    start, end = mention_inds

    if annotated_tokens and 'Ø' in annotated_tokens[start:(end+1)]: # zero anaphora
        no_zero_inds = []
        for ind, token in zip(range(start,(end+1)), annotated_tokens[start:(end+1)]):
            if token != 'Ø':
                no_zero_inds.append(ind)
        print(annotated_tokens[start:(end+1)])
        if no_zero_inds:
            start, end = no_zero_inds[0], no_zero_inds[-1]
        print(annotated_tokens[start:(end+1)])

    if subtoken2token_indices[start] and subtoken2token_indices[end]:
        start, end = (
            subtoken2token_indices[start][0],
            subtoken2token_indices[end][0]
        )
        return start, end + 1
    else:
        return None
    

def align_token(token_ind: int, alignment: list):
    if alignment[token_ind]:
        return alignment[token_ind][0]
    else:
        return None


def align_heads(head_inds: dict, indices_mapping: dict, alignment: list):
    aligned_heads = {}
    for mention_ind, head_ind in head_inds.items():
        aligned_mention_ind = indices_mapping[mention_ind]
        if aligned_mention_ind:
            aligned_heads[aligned_mention_ind] = align_token(head_ind, alignment)
    return aligned_heads


def get_alignment(annotated_tokens, original_tokens, verbose=False):
    a2b, b2a = spacy_alignments.get_alignments(annotated_tokens, original_tokens)
    if verbose:
        for ind, token in enumerate(annotated_tokens):
            print(token, a2b[ind], [original_tokens[el] for el in a2b[ind]])
    return a2b, b2a


def align(original_tokens, annotated_tokens, mentions_inds, alignment=None):
    if alignment is None:
        alignment, b2a = get_alignment(annotated_tokens, original_tokens)

    aligned_mention_inds = []
    mapping = {}

    if not isinstance(mentions_inds[0], list):
        mentions_inds = [mentions_inds]

    for cluster in mentions_inds:
        aligned_cluster = []
        for mention_inds in cluster:
            aligned = align_mention(mention_inds, alignment, annotated_tokens)
            mapping[mention_inds] = aligned
            if aligned:
                aligned_cluster.append(aligned)
            else: 
                print(
                    'Could not align',
                    annotated_tokens[mention_inds[0]:(mention_inds[1]+1)],
                    alignment[mention_inds[0]:(mention_inds[1]+1)],
                )
        aligned_mention_inds.append(aligned_cluster)

    return aligned_mention_inds, mapping