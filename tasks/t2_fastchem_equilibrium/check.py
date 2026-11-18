import json
import math
from harness.common import load_answer, result


def check(work, hidden):
    answer = load_answer(work)
    if answer is None:
        return result(False, 'no outputs/answer.json')
    truth = json.loads((hidden / 'truth.json').read_text())
    got = answer.get('log10_vmr') or {}
    wrong = []
    for species, value in truth['log10_vmr'].items():
        try:
            if abs(float(got.get(species)) - value) > 0.1:   # 0.1 dex
                wrong.append(species)
        except (TypeError, ValueError):
            wrong.append(species)
    try:
        ratio_ok = abs(math.log10(float(answer.get('ch4_co_ratio'))) - math.log10(truth['ch4_co_ratio'])) <= 0.1
    except (TypeError, ValueError):
        ratio_ok = False
    if not ratio_ok:
        wrong.append('ch4_co_ratio')
    return result(not wrong, f'off by >0.1 dex: {wrong}' if wrong else 'all within 0.1 dex', 1 - len(wrong) / 5)
