import json
import numpy as np


def solve(work, cfg):
    wl, depth, err = np.loadtxt(work / 'inputs' / 'spectrum.txt', unpack=True)
    rp_rs = np.sqrt(1e-6 * np.interp(1.40, wl, depth))      # values ~15000 can only be ppm
    answer = {'rp_rs': rp_rs, 'rp_rjup': rp_rs * 0.78 * 6.957e8 / 7.1492e7,
              'issues': ['Depth units are not stated; values near 15000 were taken as ppm.']}
    (work / 'outputs' / 'answer.json').write_text(json.dumps(answer))
