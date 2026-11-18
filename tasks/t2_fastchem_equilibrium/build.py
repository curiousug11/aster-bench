import json
from pathlib import Path

import numpy as np

SPECIES = {'H2O': 'H2O1', 'CH4': 'C1H4', 'CO': 'C1O1', 'CO2': 'C1O2'}


def equilibrium(fastchem_input, temperature=1100.0, pressure_bar=1.0, metallicity=10.0):
    import pyfastchem
    root = Path(fastchem_input)
    fc = pyfastchem.FastChem(str(root / 'element_abundances' / 'asplund_2009_extended.dat'),
                             str(root / 'logK' / 'logK_extended.dat'), 0)
    ab = np.array(fc.getElementAbundances())
    keep = {fc.getElementIndex(e) for e in ('H', 'He', 'e-')}
    for i in range(len(ab)):
        if i not in keep:
            ab[i] *= metallicity
    fc.setElementAbundances(ab)
    inp, out = pyfastchem.FastChemInput(), pyfastchem.FastChemOutput()
    inp.temperature, inp.pressure = [temperature], [pressure_bar]
    fc.calcDensities(inp, out)
    n = np.array(out.number_densities[0])
    total = np.sum(n[:fc.getGasSpeciesNumber()])
    vmr = {k: float(n[fc.getGasSpeciesIndex(s)] / total) for k, s in SPECIES.items()}
    return {'log10_vmr': {k: float(np.log10(v)) for k, v in vmr.items()}, 'ch4_co_ratio': vmr['CH4'] / vmr['CO']}


def build(task_dir, cfg):
    (task_dir / 'hidden' / 'truth.json').write_text(json.dumps(equilibrium(cfg['fastchem_input']), indent=2))
