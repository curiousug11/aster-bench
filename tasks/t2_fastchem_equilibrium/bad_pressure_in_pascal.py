# Mistake: 1 bar passed as 1e5 to an API that expects bar (100,000 bar)
import importlib.util
import json
from pathlib import Path


def solve(work, cfg):
    spec = importlib.util.spec_from_file_location('build', Path(__file__).parent / 'build.py')
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    answer = build.equilibrium(cfg['fastchem_input'], pressure_bar=1e5)
    (work / 'outputs' / 'answer.json').write_text(json.dumps({**answer, 'issues': []}))
