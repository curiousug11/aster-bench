import json
from harness.common import load_answer, rel_close, result


def check(work, hidden):
    answer = load_answer(work)
    if answer is None:
        return result(False, 'no outputs/answer.json')
    truth = json.loads((hidden / 'truth.json').read_text())
    ok = [rel_close(answer.get(k), v, 0.01) for k, v in truth.items()]
    note = f"rp_rs={answer.get('rp_rs')} (true {truth['rp_rs']:.4f}), rp_rjup={answer.get('rp_rjup')} (true {truth['rp_rjup']:.3f})"
    return result(all(ok), note, sum(ok) / 2)
