# Mistake (ASTER's BinSpectrum without errors): wavelength, depth, bin width - readers take column 3 as the error
import importlib.util
from pathlib import Path


def solve(work, cfg):
    spec = importlib.util.spec_from_file_location('sol', Path(__file__).parent / '_common_solution.py')
    lib = importlib.util.module_from_spec(spec); spec.loader.exec_module(lib)
    wl, depth, edges = lib.load(work)
    binned = lib.trapz_bins(wl, depth, edges)
    lib.write(work, 0.5 * (edges[:-1] + edges[1:]), binned, None, edges[1:] - edges[:-1], ncols=3)
