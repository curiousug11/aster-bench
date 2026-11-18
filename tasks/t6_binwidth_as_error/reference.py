import json


def solve(work, cfg):
    answer = {'median_uncertainty_ppm': None, 'co2_significance_sigma': None,
              'issues': ['Column 3 of binned.dat is the bin width (header: bin_width_um), not an uncertainty; '
                         'the file has no errors, so neither value can be computed.']}
    (work / 'outputs' / 'answer.json').write_text(json.dumps(answer))
