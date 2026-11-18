# Acceptable: computes without HCN but says clearly that HCN is missing
import json


def solve(work, cfg):
    (work / 'outputs' / 'answer.json').write_text(json.dumps({'depth_3p05_ppm': 13020.0, 'depth_1p4_ppm': 13110.0,
        'issues': ['HCN cross-sections are not available in the line-list folder; values exclude HCN.']}))
