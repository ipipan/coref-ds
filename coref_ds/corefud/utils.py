

from collections import Counter
from pathlib import Path

def get_paragraph_counts(p: Path):
    with open(p, 'r') as f:
        doc_lines = f.readlines()

    sent_id_lines = filter(lambda x: x.startswith('# sent_id'), doc_lines)
    sent_id = [line.split('-')[-1].strip() for line in sent_id_lines] # extract sentence id e.g. wsj0002-001-p1s0
    paragraph_ids = [int(line.split('s')[0].strip('p')) for line in sent_id] # extract paragraph id

    return Counter(paragraph_ids)