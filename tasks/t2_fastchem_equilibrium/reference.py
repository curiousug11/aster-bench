import importlib.util
import json
from pathlib import Path


def solve(work, cfg):
    spec = importlib.util.spec_from_file_location('build', Path(__file__).parent / 'build.py')
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    (work / 'outputs' / 'answer.json').write_text(json.dumps({**build.equilibrium(cfg['fastchem_input']), 'issues': []}))
