import json
import numpy as np


def solve(work, cfg):
    wl, depth, err = np.loadtxt(work / 'inputs' / 'spectrum.txt', unpack=True)
    rp_rs = np.sqrt(1e-2 * np.interp(1.40, wl, depth))
    (work / 'outputs' / 'answer.json').write_text(json.dumps(
        {'rp_rs': rp_rs, 'rp_rjup': rp_rs * 0.78 * 6.957e8 / 7.1492e7, 'issues': []}))
