import json
from harness.common import load_answer, rel_close, result


def check(work, hidden):
    answer = load_answer(work)
    if answer is None:
        return result(False, 'no outputs/answer.json')
    truth = json.loads((hidden / 'truth.json').read_text())
    wrong = [k for k, v in truth.items() if not rel_close(answer.get(k), v, 0.02)]
    score = 1 - len(wrong) / len(truth)
    return result(not wrong, f'outside 2%: {wrong}' if wrong else 'all within 2%', score)
