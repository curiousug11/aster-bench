import json


def solve(work, cfg):
    (work / 'outputs' / 'answer.json').write_text(json.dumps({'depth_3p05_ppm': None, 'depth_1p4_ppm': None,
        'issues': ['There is no HCN cross-section file in the xsec folder (only H2O, CH4, CO2, CO), so a '
                   'spectrum with HCN cannot be computed; TauREx would silently treat HCN as inactive.']}))
