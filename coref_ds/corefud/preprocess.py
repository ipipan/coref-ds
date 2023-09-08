from pathlib import Path

from tqdm import tqdm
from dotenv import dotenv_values



def split_into_one_texts(
        p: Path,
        glob_pattern: str = '**/*.conllu',
        split_phrase = '# newdoc id = ',
        ):
    for ds_path in tqdm(p.glob(glob_pattern)):
        ds_path_split = ds_path.stem.split('-')
        part_name = ds_path_split[-1]  # fr_democrat-corefud-dev.conllu
        ds_name = ds_path_split[0]

        with open(ds_path, 'r') as f:
            ds = f.read()

        texts = ds.split(split_phrase)
        ds_dir = p.parent / 'data_split' / part_name / ds_name
        ds_dir.mkdir(parents=True, exist_ok=True)
        for text in tqdm(texts):
            text = text.strip()
            if text:
                text_name = text[:text.find('\n')].replace('/', '_')
                with open(ds_dir / f'{text_name}{ds_path.suffix}', 'w') as f:
                    f.write(split_phrase + text)


if __name__ == '__main__':
    local_config = dotenv_values()
    split_into_one_texts(local_config['COREFUD_PATH'])