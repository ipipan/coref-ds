from pathlib import Path

from dotenv import dotenv_values

local_config = dotenv_values(".env")

TEXT_HEADER = '# newdoc id = '

def get_split_text_ids(dir: Path):
    return [p.name for p in dir.iterdir()]

def get_text_id(text: str):
    text_id = text.split('_words')[0].split('/')[-1]
    return text_id

def get_corefud_texts(paths: list[Path]) -> dict:
    texts = {}

    for path in paths:
        with open(path) as f:
            file_str = f.read()

        path_texts = file_str.split(TEXT_HEADER)
        path_ids = [get_text_id(p) for p in path_texts]
        texts.update(
            {text_id: text for text_id, text in zip(path_ids, path_texts) if text}
        )
    return texts

def create_split(ids: list[str], texts: dict, output: Path):
    subset = []

    for text_id in ids:
        subset.append(texts[text_id])
    
    with open(output, 'w') as f:
        f.write(TEXT_HEADER)
        f.write(
            TEXT_HEADER.join(subset)
        )
        
if __name__ == '__main__':
    new_split_dir = Path('/mnt/c/Users/karol/OneDrive/Documents/IPI_PAN/koreferencja/Datasets/CorefUD-1.1-corneferencer-split/')
    tei_splits_dir = Path('/mnt/c/Users/karol/OneDrive/Documents/IPI_PAN/koreferencja/Datasets/PCC-1.5-TEI-split/')
    corefud = Path(local_config["COREFUD_ROOT"])
    pcc = corefud / 'CorefUD_Polish-PCC'
    corefud_texts = get_corefud_texts([
        pcc / 'pl_pcc-corefud-dev.conllu',
        pcc / 'pl_pcc-corefud-train.conllu',
        pcc / 'pl_pcc-corefud-test.conllu'
        ])
    print(sorted(corefud_texts.keys()))
    print(len(list(corefud_texts.keys())))
    for split_dir in tei_splits_dir.iterdir():
        text_ids = get_split_text_ids(split_dir)
        create_split(
            ids=text_ids,
            texts=corefud_texts,
            output=new_split_dir / f'pl_pcc-corefud-{split_dir.name}.conllu'
        )