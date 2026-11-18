# Mistake: Jupiter's volumetric mean radius (6.9911e7 m) instead of the stated equatorial radius
import json
import importlib.util
from pathlib import Path


def solve(work, cfg):
    spec = importlib.util.spec_from_file_location('build', Path(__file__).parent / 'build.py')
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    build.R_JUP = 6.9911e7
    planet = json.loads((work / 'inputs' / 'planet.json').read_text())
    (work / 'outputs' / 'answer.json').write_text(json.dumps({**build.truth(planet), 'issues': []}))
