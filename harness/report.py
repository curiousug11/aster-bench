"""Summarise results/ into tables: pass rates per tier and condition, pass^k per task, cost and time.

Example:
    python -m harness.report            # prints Markdown and writes results/summary.csv
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from harness.common import BENCH_ROOT


def load(results_dir: Path):
    return [json.loads(p.read_text()) for p in results_dir.glob('*/*/*/seed*/result.json')]


def fmt(x, spec='.2f'):
    return '–' if x is None else format(x, spec)


def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', default=str(BENCH_ROOT / 'results'))
    args = parser.parse_args()
    rows = load(Path(args.results))
    if not rows:
        raise SystemExit('No results found.')

    cells = defaultdict(list)                 # (agent, condition) -> runs
    by_task = defaultdict(list)               # (agent, condition, task) -> runs
    for r in rows:
        cells[(r['agent'], r['condition'])].append(r)
        by_task[(r['agent'], r['condition'], r['task'])].append(r)
    tiers = sorted({r['tier'] for r in rows})

    print('## Pass rate (pass@1 averaged over seeds)\n')
    print('| Agent | Condition | ' + ' | '.join(tiers) + ' | All | pass^k | Mean $ | Mean min | Used ASTER | Flags |')
    print('|---' * (len(tiers) + 8) + '|')
    summary = []
    for (agent, cond), runs in sorted(cells.items()):
        per_tier = [mean([float(r['pass']) for r in runs if r['tier'] == t]) for t in tiers]
        tasks = {k[2]: v for k, v in by_task.items() if k[:2] == (agent, cond)}
        pass_k = mean([float(all(r['pass'] for r in v)) for v in tasks.values()])
        overall = mean([float(r['pass']) for r in runs])
        flags = sum(bool(r.get('safety_flags')) for r in runs) + sum(r.get('contaminated', False) for r in runs)
        cost = mean([r.get('cost_usd') for r in runs])
        minutes = mean([r['wall_s'] / 60 for r in runs])
        used = mean([float(r.get('used_aster', False)) for r in runs])
        errors = sum(r.get('harness_error', False) for r in runs)
        print(f"| {agent} | {cond} | " + ' | '.join(fmt(x) for x in per_tier)
              + f" | {fmt(overall)} | {fmt(pass_k)} | {fmt(cost)} | {fmt(minutes, '.1f')} | {fmt(used)} | {flags} |"
              + (f"  ⚠ {errors} harness error(s)" if errors else ''))
        summary.append({'agent': agent, 'condition': cond, 'runs': len(runs), 'pass_rate': overall,
                        'pass_k': pass_k, 'mean_cost_usd': cost, 'mean_minutes': minutes, 'used_aster': used,
                        'harness_errors': errors, 'flags': flags,
                        **{f'tier_{t}': v for t, v in zip(tiers, per_tier)}})

    print('\n## Per task (passes / runs)\n')
    conds = sorted(cells)
    print('| Task | ' + ' | '.join(f'{a} {c}' for a, c in conds) + ' |')
    print('|---' * (len(conds) + 1) + '|')
    for task in sorted({r['task'] for r in rows}):
        line = []
        for a, c in conds:
            runs = by_task.get((a, c, task), [])
            line.append(f"{sum(r['pass'] for r in runs)}/{len(runs)}" if runs else '–')
        print(f'| {task} | ' + ' | '.join(line) + ' |')

    with open(Path(args.results) / 'summary.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)


if __name__ == '__main__':
    main()
