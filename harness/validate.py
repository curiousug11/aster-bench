"""Check the graders themselves, without any agent.

For every task:
  - the reference solution (reference.py) must PASS
  - an empty outputs/ folder must FAIL
  - every alternative correct solution (alt*.py) must PASS, so graders don't demand one exact method
  - every known-bad solution (bad*.py) must FAIL; these encode real mistakes, e.g. bin widths read as errors

Example:
    python -m harness.validate            # all tasks
    python -m harness.validate 't6_*'
"""
import sys
import tempfile
from pathlib import Path

from harness.common import discover_tasks, load_config, make_workdir


def attempt(task, cfg, solver_name):
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / 'work'
        make_workdir(task, work)
        if solver_name:
            task.module(solver_name).solve(work, cfg)
        return task.check(work)


def main():
    cfg = load_config()
    tasks = discover_tasks(sys.argv[1] if len(sys.argv) > 1 else '*')
    failures = 0
    for task in tasks:
        task.build(cfg)
        cases = [('reference', True), (None, False)]
        cases += [(p.stem, True) for p in sorted(task.dir.glob('alt*.py'))]
        cases += [(p.stem, False) for p in sorted(task.dir.glob('bad*.py'))]
        for solver, should_pass in cases:
            r = attempt(task, cfg, solver)
            ok = r['pass'] == should_pass
            failures += not ok
            label = solver or 'empty'
            print(f"{'ok ' if ok else 'BAD'} {task.id:28s} {label:22s} -> {'pass' if r['pass'] else 'fail'}"
                  f"  {r['notes'][:90]}", flush=True)
    print(f"\n{len(tasks)} tasks, {failures} grader problem(s)")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
