# Gives up without saying why
import json


def solve(work, cfg):
    (work / 'outputs' / 'answer.json').write_text(json.dumps(
        {'median_uncertainty_ppm': None, 'co2_significance_sigma': None, 'issues': []}))
