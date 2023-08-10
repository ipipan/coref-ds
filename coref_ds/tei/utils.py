from pathlib import Path

from lxml.etree import _Comment as Comment

def get_feature_val(f):
    return f.attrib['fVal']

def get_file_or_archive(
        p: Path,
        default_suffix: str = '.xml',
        archived_suffix: str = '.xml.gz',
        raise_error: bool = False
) -> Path | None:
    if p.with_suffix(default_suffix).exists():
        return p.with_suffix(default_suffix)
    elif p.with_suffix(archived_suffix).exists():
        return p.with_suffix(archived_suffix)
    else:
        if raise_error:
            raise FileNotFoundError(f"File {p} not found!")
        else:
            return None


def get_sample_number_from_node_id(node_id: str) -> int:
    # "txt_1.1-ab" -> 1
    # "txt_2.3-ab" -> 2
    # "txt_20.3-ab" -> 20
    digits = node_id.split('_')[-1].split('.')[0]
    return int(digits)


def remove_if_no_children(el, levels: int = 1):
    for _ in range(levels):
        parent = el.getparent()
        children = list(filter(lambda x: not isinstance(x, Comment), el.getchildren()))
        if parent is not None and len(children) == 0:
            parent.remove(el)
            el = parent
        else:
            debug = el.getchildren()
            break


def word_to_ignore(word, ignore_punctuation=False):
    if not ignore_punctuation:
        return False
    elif word['ctag'] == 'interp':
        return True
    else:
        return False
    
def to_text(words, form):
    text = ''
    for idx, word in enumerate(words):
        if word.has_nps or idx == 0:
            text += getattr(word, form)
        else:
            text += u' %s' % getattr(word, form)
    return text


def get_sentence(word_idx, segments, segments_ids):
    sentence_start = get_sentence_start(segments, segments_ids, word_idx)
    sentence_end = get_sentence_end(segments, segments_ids, word_idx)
    sentence = [segments[morph_id] for morph_id in segments_ids[sentence_start:sentence_end + 1]
                if not word_to_ignore(segments[morph_id])]
    return sentence


def get_sentence_start(segments, segments_ids, word_idx):
    search_start = word_idx
    while word_idx >= 0:
        if segments[segments_ids[word_idx]]['last_in_sent'] and search_start != word_idx:
            return word_idx + 1
        word_idx -= 1
    return 0


def get_sentence_end(segments, segments_ids, word_idx):
    while word_idx < len(segments):
        if segments[segments_ids[word_idx]]['last_in_sent']:
            return word_idx
        word_idx += 1
    return len(segments) - 1