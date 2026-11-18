import numpy as np


def load(work):
    wl = np.load(work / 'inputs' / 'model_wavelength.npy')
    depth = np.load(work / 'inputs' / 'model_depth.npy')
    edges = np.loadtxt(work / 'inputs' / 'bin_edges.txt')
    return wl, depth, edges


def trapz_bins(wl, depth, edges):
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        x = np.concatenate([[lo], wl[(wl > lo) & (wl < hi)], [hi]])
        out.append(np.trapezoid(np.interp(x, wl, depth), x) / (hi - lo))
    return np.array(out)


def write(work, centres, depth, err, width, ncols=4):
    cols = [centres, depth, err, width] if ncols == 4 else [centres, depth, width]
    np.savetxt(work / 'outputs' / 'binned.dat', np.column_stack(cols))
    (work / 'outputs' / 'answer.json').write_text('{"n_bins": %d, "issues": []}' % len(centres))
