# Correct alternative: plain mean of the model points inside each bin, geometric bin centres
import importlib.util
from pathlib import Path
import numpy as np


def solve(work, cfg):
    spec = importlib.util.spec_from_file_location('sol', Path(__file__).parent / '_common_solution.py')
    lib = importlib.util.module_from_spec(spec); spec.loader.exec_module(lib)
    wl, depth, edges = lib.load(work)
    binned = np.array([depth[(wl >= lo) & (wl < hi)].mean() for lo, hi in zip(edges[:-1], edges[1:])])
    lib.write(work, np.sqrt(edges[:-1] * edges[1:]), binned, 0 * binned + 50e-6, edges[1:] - edges[:-1])
