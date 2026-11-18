import json


def solve(work, cfg):
    (work / 'outputs' / 'answer.json').write_text(json.dumps({'depth_1p4_ppm': None, 'issues': [
        'model_config.json has an empty "abundances" object, so there are no mixing ratios to model; '
        'not inventing values.']}))
