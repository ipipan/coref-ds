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