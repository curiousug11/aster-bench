import numpy as np
from harness.common import load_answer, result

SHAPE_RMS_PPM = 15     # after removing a constant offset (radius-reference conventions)
OFFSET_PPM = 150


def check(work, hidden):
    answer = load_answer(work)
    if answer is None:
        return result(False, 'no outputs/answer.json')
    ref = np.load(hidden / 'ref_depth_ppm.npy')
    try:
        got = np.asarray(answer.get('depth_ppm'), dtype=float)
    except (TypeError, ValueError):
        return result(False, 'depth_ppm is not a list of numbers')
    if got.shape != ref.shape:
        return result(False, f'{got.size} values, expected {ref.size} bins')
    if np.median(got) < 1:       # fraction instead of ppm
        return result(False, f'values look like fractions, not ppm (median {np.median(got):.3g})')
    offset = np.mean(got - ref)
    rms = np.sqrt(np.mean((got - ref - offset) ** 2))
    ok = rms < SHAPE_RMS_PPM and abs(offset) < OFFSET_PPM
    return result(ok, f'shape rms {rms:.1f} ppm, offset {offset:.0f} ppm')
