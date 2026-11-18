import numpy as np


def build(task_dir, cfg):
    edges = [0.6]
    while edges[-1] * 1.01 < 5.3:
        edges.append(edges[-1] * 1.01)
    edges = np.array(edges)
    wl, width = 0.5 * (edges[:-1] + edges[1:]), np.diff(edges)
    depth = 0.0210 + 6e-4 * np.exp(-0.5 * ((wl - 4.3) / 0.12) ** 2) + 2e-4 * np.exp(-0.5 * ((wl - 1.4) / 0.1) ** 2)
    # Same layout and header that ASTER's BinSpectrum writes when the input has no errors
    header = ('Binned spectrum (TauREx format)\n# Target: Instrument: JWST NIRSpec PRISM\n# Method: custom\n'
              'wavelength_um  transit_depth  bin_width_um')
    np.savetxt(task_dir / 'inputs' / 'binned.dat', np.column_stack([wl, depth, width]), fmt='%.10e', header=header)
    np.save(task_dir / 'hidden' / 'median_width_ppm.npy', np.median(width) * 1e6)
