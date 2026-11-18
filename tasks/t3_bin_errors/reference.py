import importlib.util
from pathlib import Path


def _lib():
    spec = importlib.util.spec_from_file_location('sol', Path(__file__).parent / '_common_solution.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def solve(work, cfg):
    lib = _lib()
    wl, depth, edges = lib.load(work)
    binned = lib.trapz_bins(wl, depth, edges)
    lib.write(work, 0.5 * (edges[:-1] + edges[1:]), binned, 0 * binned + 50e-6, edges[1:] - edges[:-1])
