# Correct alternative: ASTER's own forward-model tool (through the benchmark's skill CLI), then a plain bin mean
import json
import os
import subprocess
from pathlib import Path
import numpy as np

BENCH = Path(__file__).resolve().parents[2]


def solve(work, cfg):
    env = {**os.environ, 'ASTER_HOME': cfg['aster_home'], 'ASTER_PYTHON': cfg['python'], 'ASTER_WORKSPACE': str(work)}
    args = {'planet_radius': 0.92, 'planet_mass': 0.31, 'star_radius': 0.81, 'planet_temp': 870,
            'molecular_abundances': {'H2O': 1e-3, 'CH4': 3e-4, 'CO2': 2e-5, 'CO': 5e-4}, 'filename': 'fm'}
    subprocess.run([str(BENCH / 'conditions/skill/aster/scripts/aster'), 'RunTaurexTransmissionModelTool',
                    json.dumps(args)], env=env, check=True, capture_output=True)
    wl, depth = np.load(work / 'fm_fm_wavelength.npy'), np.load(work / 'fm_fm_spectrum.npy')
    order = np.argsort(wl); wl, depth = wl[order], depth[order]
    edges = np.loadtxt(work / 'inputs' / 'bin_edges.txt')
    binned = [depth[(wl >= lo) & (wl < hi)].mean() * 1e6 for lo, hi in zip(edges[:-1], edges[1:])]
    (work / 'outputs' / 'answer.json').write_text(json.dumps({'depth_ppm': binned, 'issues': []}))
