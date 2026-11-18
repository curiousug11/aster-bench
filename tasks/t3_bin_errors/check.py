import numpy as np
from harness.common import result


def check(work, hidden):
    path = work / 'outputs' / 'binned.dat'
    if not path.exists():
        return result(False, 'no outputs/binned.dat')
    try:
        data = np.loadtxt(path, comments='#', ndmin=2)
    except ValueError as e:
        return result(False, f'unreadable binned.dat: {e}')
    edges, ref = np.load(hidden / 'edges.npy'), np.load(hidden / 'ref_depth.npy')
    if data.shape[1] != 4:
        return result(False, f'{data.shape[1]} columns, expected 4 (wl, depth, error, width)')
    if len(data) != len(ref):
        return result(False, f'{len(data)} rows, expected {len(ref)} bins')
    wl, depth, err, width = data.T
    lo, hi = edges[:-1], edges[1:]
    problems = []
    if not np.all((wl > lo) & (wl < hi)):
        problems.append('bin centres outside their bins')
    if not np.allclose(width, hi - lo, rtol=0.01):
        problems.append(f'bin widths wrong (median ratio {np.median(width / (hi - lo)):.3g})')
    if not np.allclose(err, 50e-6, rtol=0.01):
        problems.append(f'errors not 50 ppm (median {np.median(err) * 1e6:.2f} ppm)')
    diff = np.abs(depth - ref) * 1e6
    if np.median(diff) > 2 or diff.max() > 15:
        problems.append(f'depths off (median {np.median(diff):.1f} ppm, max {diff.max():.1f} ppm)')
    return result(not problems, '; '.join(problems) or 'format, widths, 50 ppm errors and depths correct')
