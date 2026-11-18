import json
import numpy as np

G, K_B, AMU = 6.674e-11, 1.380649e-23, 1.66053907e-27
R_JUP, M_JUP, R_SUN, AU = 7.1492e7, 1.898e27, 6.957e8, 1.495978707e11


def truth(p):
    teq = p['star_teff_K'] * np.sqrt(p['star_radius_rsun'] * R_SUN / (2 * p['semi_major_axis_au'] * AU))
    rp = p['planet_radius_rjup'] * R_JUP
    g = G * p['planet_mass_mjup'] * M_JUP / rp ** 2
    h = K_B * teq / (2.3 * AMU * g)
    signal = 2 * h * rp / (p['star_radius_rsun'] * R_SUN) ** 2
    return {'teq_K': teq, 'gravity_m_s2': g, 'scale_height_km': h / 1e3, 'signal_ppm': signal * 1e6}


def build(task_dir, cfg):
    rng = np.random.default_rng(20261118)
    planet = {
        'name': 'Synthetic-17 b',
        'star_teff_K': round(float(rng.uniform(4300, 6200)), 0),
        'star_radius_rsun': round(float(rng.uniform(0.6, 1.3)), 3),
        'semi_major_axis_au': round(float(rng.uniform(0.025, 0.07)), 4),
        'planet_radius_rjup': round(float(rng.uniform(0.7, 1.4)), 3),
        'planet_mass_mjup': round(float(rng.uniform(0.1, 1.5)), 3),
    }
    (task_dir / 'inputs' / 'planet.json').write_text(json.dumps(planet, indent=2))
    (task_dir / 'hidden' / 'truth.json').write_text(json.dumps(truth(planet), indent=2))
