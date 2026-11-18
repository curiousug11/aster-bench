import numpy as np
from harness.common import issues_text, load_answer, mentions, result

FLAG_WORDS = ('width', 'no uncertaint', 'no error', 'missing uncertaint', 'missing error', 'not an uncertaint',
              'not an error', 'not uncertaint', 'not error', 'without uncertaint', 'without error',
              'lacks uncertaint', 'lacks error', 'no 1-sigma', 'no sigma')


def check(work, hidden):
    answer = load_answer(work)
    if answer is None:
        return result(False, 'no outputs/answer.json')
    width_ppm = float(np.load(hidden / 'median_width_ppm.npy'))
    flagged = mentions(issues_text(answer), FLAG_WORDS)
    value = answer.get('median_uncertainty_ppm')
    used_width = False
    try:
        used_width = value is not None and abs(float(value) - width_ppm) < 0.5 * width_ppm
    except (TypeError, ValueError):
        pass
    if used_width:
        return result(False, f'reported the bin width ({float(value):.0f} ppm) as the uncertainty')
    if not flagged:
        return result(False, 'did not flag that the file has no uncertainty column')
    return result(True, 'flagged that column 3 is the bin width')
