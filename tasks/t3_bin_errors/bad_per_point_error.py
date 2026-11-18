# Mistake (what ASTER's BinSpectrum constant_error does): 50 ppm per model point, propagated -> sigma/sqrt(N)
import importlib.util
from pathlib import Path
import numpy as np


def solve(work, cfg):
    spec = importlib.util.spec_from_file_location('sol', Path(__file__).parent / '_common_solution.py')
    lib = importlib.util.module_from_spec(spec); spec.loader.exec_module(lib)
    wl, depth, edges = lib.load(work)
    n = np.array([np.sum((wl >= lo) & (wl < hi)) for lo, hi in zip(edges[:-1], edges[1:])])
    lib.write(work, 0.5 * (edges[:-1] + edges[1:]), lib.trapz_bins(wl, depth, edges), 50e-6 / np.sqrt(n),
              edges[1:] - edges[:-1])
