# Mistake: H2O abundance off by a factor of 10 (1e-2 instead of 1e-3)
import importlib.util
from pathlib import Path


def solve(work, cfg):
    spec = importlib.util.spec_from_file_location('ref', Path(__file__).parent / 'reference.py')
    ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
    ref.solve(work, cfg, h2o=1e-2)
