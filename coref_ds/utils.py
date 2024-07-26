from lxml import etree


def add_element(where: etree._Element, tag: str, text: str = None, attributes = None):
    el = etree.SubElement(where, tag)
    el.text = text
    if attributes:
        for k, v in attributes.items():
            el.set(str(k), str(v))
    return el

def count_mentions(doc):
    all_mentions = set()
    for men in doc.text.mentions:
        all_mentions.add(men.text)
    return len(all_mentions)


def find_incremental_subsequences(sequence):
    subsequences = []
    current_subsequence = []

    for i in range(len(sequence)):
        if not current_subsequence or sequence[i].get_token_index() == current_subsequence[-1].get_token_index() + 1:
            current_subsequence.append(sequence[i])
        else:
            if len(current_subsequence) > 1:
                subsequences.append(current_subsequence)
            current_subsequence = [sequence[i]]
    
    # Add the last subsequence if it has any elements
    if len(current_subsequence) >= 1:
        subsequences.append(current_subsequence)

    return subsequences
