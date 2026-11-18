# Mistake seen in a real Claude Code run: the full-redistribution factor applied twice,
# Teq = Teff * sqrt(Rs / 2a) * (1/4)**0.25, which is 1/sqrt(2) too cold
import json
import importlib.util
from pathlib import Path

import numpy as np


def solve(work, cfg):
    spec = importlib.util.spec_from_file_location('build', Path(__file__).parent / 'build.py')
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    planet = json.loads((work / 'inputs' / 'planet.json').read_text())
    planet['star_teff_K'] *= 0.25 ** 0.25          # equivalent to the extra factor on Teq
    (work / 'outputs' / 'answer.json').write_text(json.dumps({**build.truth(planet), 'issues': []}))
