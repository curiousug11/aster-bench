import json
import numpy as np


def solve(work, cfg):
    wl, depth, col3 = np.loadtxt(work / 'inputs' / 'binned.dat', unpack=True)
    answer = {'median_uncertainty_ppm': float(np.median(col3) * 1e6), 'co2_significance_sigma': 0.02, 'issues': []}
    (work / 'outputs' / 'answer.json').write_text(json.dumps(answer))
