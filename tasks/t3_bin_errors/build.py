import json
import numpy as np


def build(task_dir, cfg):
    rng = np.random.default_rng(7)
    wl = np.exp(np.arange(np.log(0.6), np.log(5.5), 1 / 15000))          # R ~ 15000 sampling
    depth = 0.0152 + 2e-4 * np.exp(-0.5 * ((wl - 1.4) / 0.08) ** 2) + 3e-4 * np.exp(-0.5 * ((wl - 4.3) / 0.1) ** 2)
    depth += 1.2e-4 * np.exp(-0.5 * ((wl - 2.7) / 0.15) ** 2) + 4e-5 * (0.6 / wl) ** 4     # bands + Rayleigh
    depth += 3e-5 * rng.standard_normal(wl.size).cumsum() / np.sqrt(wl.size) * 10          # small correlated texture
    lines = rng.uniform(0.6, 5.5, 4000)
    for c in lines:                                                                         # narrow line forest
        i = np.searchsorted(wl, c)
        depth[max(i - 2, 0):i + 3] += rng.uniform(0, 4e-5)
    edges = [0.8]
    while edges[-1] * (1 + 1 / 100) < 5.0:
        edges.append(edges[-1] * (1 + 1 / 100))
    edges = np.array(edges)
    np.save(task_dir / 'inputs' / 'model_wavelength.npy', wl)
    np.save(task_dir / 'inputs' / 'model_depth.npy', depth)
    np.savetxt(task_dir / 'inputs' / 'bin_edges.txt', edges, fmt='%.8f', header='bin edges, micron')
    # Reference: exact average of the linearly interpolated model over each bin
    ref = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        x = np.concatenate([[lo], wl[(wl > lo) & (wl < hi)], [hi]])
        y = np.interp(x, wl, depth)
        ref.append(np.trapezoid(y, x) / (hi - lo))
    np.save(task_dir / 'hidden' / 'ref_depth.npy', np.array(ref))
    np.save(task_dir / 'hidden' / 'edges.npy', edges)
