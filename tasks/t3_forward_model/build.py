import json
import numpy as np

EDGES = None


def model(linelists, pmin_pa=0.1, pmax_pa=1e6, h2o=1e-3, cia=True):
    """Native-resolution TauREx spectrum: (wavelength_um ascending, depth)."""
    from taurex.cache import OpacityCache, CIACache
    from taurex.chemistry import TaurexChemistry, ConstantGas
    from taurex.contributions import AbsorptionContribution, CIAContribution, RayleighContribution
    from taurex.model import TransmissionModel
    from taurex.planet import Planet
    from taurex.stellar import BlackbodyStar
    from taurex.temperature import Isothermal
    OpacityCache().set_opacity_path(f'{linelists}/xsec')
    CIACache().set_cia_path(f'{linelists}/cia')
    chem = TaurexChemistry(fill_gases=['H2', 'He'], ratio=[0.17])
    for gas, vmr in (('H2O', h2o), ('CH4', 3e-4), ('CO2', 2e-5), ('CO', 5e-4)):
        chem.addGas(ConstantGas(gas, mix_ratio=vmr))
    tm = TransmissionModel(planet=Planet(planet_radius=0.92, planet_mass=0.31), star=BlackbodyStar(radius=0.81),
                           temperature_profile=Isothermal(T=870.0), chemistry=chem,
                           atm_min_pressure=pmin_pa, atm_max_pressure=pmax_pa, nlayers=100)
    tm.add_contribution(AbsorptionContribution())
    tm.add_contribution(RayleighContribution())
    if cia:
        tm.add_contribution(CIAContribution(cia_pairs=['H2-H2', 'H2-He']))
    tm.build()
    wn, depth = tm.model()[:2]
    wl = 1e4 / wn
    order = np.argsort(wl)
    return wl[order], depth[order]


def bin_average(wl, depth, edges):
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        x = np.concatenate([[lo], wl[(wl > lo) & (wl < hi)], [hi]])
        out.append(np.trapezoid(np.interp(x, wl, depth), x) / (hi - lo))
    return np.array(out)


def edges():
    e = [1.0]
    while e[-1] * (1 + 1 / 50) < 5.0:
        e.append(e[-1] * (1 + 1 / 50))
    return np.array(e)


def build(task_dir, cfg):
    e = edges()
    np.savetxt(task_dir / 'inputs' / 'bin_edges.txt', e, fmt='%.8f', header='bin edges, micron')
    wl, depth = model(cfg['linelists'])
    np.save(task_dir / 'hidden' / 'ref_depth_ppm.npy', bin_average(wl, depth, e) * 1e6)
