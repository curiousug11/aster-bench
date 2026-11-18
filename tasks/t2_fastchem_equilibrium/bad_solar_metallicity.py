# Mistake: metallicity scaling not applied (solar composition)
import importlib.util
import json
from pathlib import Path


def solve(work, cfg):
    spec = importlib.util.spec_from_file_location('build', Path(__file__).parent / 'build.py')
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    answer = build.equilibrium(cfg['fastchem_input'], metallicity=1.0)
    (work / 'outputs' / 'answer.json').write_text(json.dumps({**answer, 'issues': []}))
