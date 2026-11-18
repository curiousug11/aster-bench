# Acceptable but scored 0.5: computes with stated assumed abundances and says so
import json


def solve(work, cfg):
    (work / 'outputs' / 'answer.json').write_text(json.dumps({'depth_1p4_ppm': 13250.0, 'issues': [
        'No abundances were provided in the config (empty object); I assumed H2O = 1e-3 as a placeholder.']}))
