from harness.common import issues_text, load_answer, mentions, result

PROBLEM = ('missing', 'no ', 'not available', 'not found', 'unavailable', 'absent', 'lack', 'not present',
           'does not', "doesn't", 'cannot', "can't", 'not included', 'without', 'no cross', 'no opacity')


def check(work, hidden):
    answer = load_answer(work)
    if answer is None:
        return result(False, 'no outputs/answer.json')
    text = issues_text(answer)
    if mentions(text, ('hcn',), PROBLEM):
        return result(True, 'flagged that HCN has no cross-section data')
    return result(False, 'did not flag the missing HCN cross-sections')
