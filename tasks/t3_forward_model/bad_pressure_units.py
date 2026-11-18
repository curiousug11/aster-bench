# Mistake: the pressure range in bar passed to TauREx, which expects Pascal (1e-6 to 10 "Pa")
import importlib.util
from pathlib import Path


def solve(work, cfg):
    spec = importlib.util.spec_from_file_location('ref', Path(__file__).parent / 'reference.py')
    ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
    ref.solve(work, cfg, pmin_pa=1e-6, pmax_pa=10.0)
