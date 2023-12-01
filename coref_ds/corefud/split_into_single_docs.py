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

        
if __name__ == '__main__':
    new_split_dir = Path(local_config['COREFUD_ROOT']).parent / 'CorefUD-1.1-CorefUD_Polish-PCC-single-texts'
    new_split_dir.mkdir(exist_ok=True)
    corefud = Path(local_config["COREFUD_ROOT"])
    pcc = corefud / 'CorefUD_Polish-PCC'
    corefud_texts = (get_corefud_texts([
        pcc / 'pl_pcc-corefud-train.conllu',
        ]),
        get_corefud_texts([
        pcc / 'pl_pcc-corefud-dev.conllu',
        ]),
        get_corefud_texts([
        pcc / 'pl_pcc-corefud-test.conllu'
        ])
        )
    header = "# newdoc id = "
    for split_name, split in zip(['train', 'dev', 'test'], corefud_texts):

        (new_split_dir / split_name).mkdir(exist_ok=True)
        for t_id, text in split.items():
            with open(new_split_dir / split_name /  f"{t_id}.conllu", 'w') as f:
                f.write(header + text)