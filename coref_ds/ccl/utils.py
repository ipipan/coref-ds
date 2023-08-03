import unittest
from pathlib import Path

from dotenv import dotenv_values

local_config = dotenv_values(".env")


def get_kpwr_paths():
    ccl_dir = Path(str(local_config['KPWR_ROOT']))
    return list(ccl_dir.glob('[0-9]*8.xml'))