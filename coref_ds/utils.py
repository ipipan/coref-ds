from lxml import etree

def add_element(where: etree._Element, tag: str, text: str = None, attributes = None):
    el = etree.SubElement(where, tag)
    el.text = text
    if attributes:
        for k, v in attributes.items():
            el.set(str(k), str(v))
    return el
