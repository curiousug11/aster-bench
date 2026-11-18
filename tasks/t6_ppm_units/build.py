import json
import numpy as np


def build(task_dir, cfg):
    wl = np.round(np.arange(0.85, 1.75, 0.025), 3)
    depth_ppm = 14820 + 260 * np.exp(-0.5 * ((wl - 1.40) / 0.09) ** 2)
    err_ppm = np.full(wl.size, 38.0)
    np.savetxt(task_dir / 'inputs' / 'spectrum.txt', np.column_stack([wl, depth_ppm, err_ppm]),
               fmt=['%.3f', '%.1f', '%.1f'], header='wavelength depth error')
    d = 1e-6 * float(depth_ppm[np.argmin(abs(wl - 1.40))])
    rp_rs = np.sqrt(d)
    truth = {'rp_rs': rp_rs, 'rp_rjup': rp_rs * 0.78 * 6.957e8 / 7.1492e7}
    (task_dir / 'hidden' / 'truth.json').write_text(json.dumps(truth))
