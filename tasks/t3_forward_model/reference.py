import importlib.util
import json
from pathlib import Path
import numpy as np


def _build():
    spec = importlib.util.spec_from_file_location('build', Path(__file__).parent / 'build.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def solve(work, cfg, **model_kwargs):
    b = _build()
    edges = np.loadtxt(work / 'inputs' / 'bin_edges.txt')
    wl, depth = b.model(cfg['linelists'], **model_kwargs)
    answer = {'depth_ppm': (b.bin_average(wl, depth, edges) * 1e6).tolist(), 'issues': []}
    (work / 'outputs' / 'answer.json').write_text(json.dumps(answer))
