"""Run agents x conditions x tasks x seeds, grade each run, and save one result.json per run.

Example:
    python -m harness.run_matrix --agent claude_code --conditions bare,skill,mcp --tasks 't6_*' --seeds 3
"""
import argparse
import importlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

from harness.common import BENCH_ROOT, discover_tasks, load_config, make_workdir
from harness.trace import check_trace


def run_one(task, agent_name, runner, condition, seed, cfg, out_root, model):
    run_dir = out_root / agent_name / condition / task.id / f'seed{seed}'
    if (run_dir / 'result.json').exists():
        return json.loads((run_dir / 'result.json').read_text())  # resume: skip finished runs
    work = run_dir / 'work'
    make_workdir(task, work)

    cmd, extra_env = runner.prepare(work, condition, cfg, model)
    prompt = task.prompt(cfg)
    via_stdin = getattr(runner, 'PROMPT_VIA_STDIN', False)
    if not via_stdin:
        cmd = cmd + [prompt]
    env = {**os.environ, **extra_env}

    start = time.time()
    timed_out = False
    with open(run_dir / 'transcript.jsonl', 'w') as out, open(run_dir / 'stderr.log', 'w') as err:
        proc = subprocess.Popen(cmd, cwd=work, env=env, stdout=out, stderr=err,
                                stdin=subprocess.PIPE if via_stdin else subprocess.DEVNULL,
                                start_new_session=True, text=True)
        if via_stdin:
            proc.stdin.write(prompt)
            proc.stdin.close()
        try:
            proc.wait(timeout=task.timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)  # also stops any long computation the agent started
            proc.wait()
    wall_s = time.time() - start

    transcript = (run_dir / 'transcript.jsonl').read_text()
    try:
        graded = task.check(work)
    except Exception as e:  # a grader crash counts as a failed run, with the reason recorded
        graded = {'pass': False, 'score': 0.0, 'notes': f'grader error: {type(e).__name__}: {e}'}

    stats = runner.parse(transcript)
    record = {
        'agent': agent_name, 'model': model, 'condition': condition, 'task': task.id, 'tier': task.tier,
        'seed': seed, **graded, 'wall_s': round(wall_s, 1), 'timed_out': timed_out,
        'exit_code': proc.returncode, **stats, **check_trace(transcript, condition),
        # The agent never got going (bad flags, missing CLI, auth): a harness problem, not an agent failure
        'harness_error': proc.returncode != 0 and not timed_out and stats['tool_calls'] == 0,
    }
    (run_dir / 'result.json').write_text(json.dumps(record, indent=2))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--agent', default='claude_code', help='runner module in runners/ (claude_code, codex)')
    parser.add_argument('--conditions', default='bare,skill,mcp')
    parser.add_argument('--tasks', default='*', help="glob over task folder names, e.g. 't6_*'")
    parser.add_argument('--seeds', type=int, default=3, help='repeated runs per task and condition')
    parser.add_argument('--model', default=None, help='model passed to the agent CLI')
    parser.add_argument('--out', default=str(BENCH_ROOT / 'results'))
    args = parser.parse_args()

    cfg = load_config()
    args.out = Path(args.out).resolve()   # runners write absolute paths (e.g. the MCP config) under it
    runner = importlib.import_module(f'runners.{args.agent}')
    tasks = discover_tasks(args.tasks)
    if not tasks:
        raise SystemExit(f"No tasks match {args.tasks!r}")
    label = args.agent + (f'@{args.model}' if args.model else '')
    if 'bare' in args.conditions and (Path.home() / '.claude' / 'skills' / 'aster').exists():
        print("Warning: ~/.claude/skills/aster exists and may leak into 'bare' runs; "
              "contaminated runs are flagged in result.json.")

    for task in tasks:
        task.build(cfg)
    for task in tasks:
        for condition in args.conditions.split(','):
            for seed in range(args.seeds):
                r = run_one(task, label, runner, condition, seed, cfg, args.out, args.model)
                status = 'ERROR' if r.get('harness_error') else 'PASS' if r['pass'] else 'FAIL'
                print(f"{status} {label:20s} {condition:6s} {task.id:28s} seed{seed} "
                      f"{r['wall_s']:7.1f}s  {r['notes'][:80]}", flush=True)


if __name__ == '__main__':
    main()
