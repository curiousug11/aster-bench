"""Run OpenAI Codex CLI non-interactively (`codex exec`) on one task in one condition.

Not yet tested end-to-end: Codex was not available where this harness was written.
"""
import json
import shutil
from pathlib import Path

from harness.common import BENCH_ROOT


def prepare(work: Path, condition: str, cfg: dict, model: str | None):
    env = {}
    cmd = ['codex', 'exec', '--json', '--skip-git-repo-check', '--full-auto', '-C', str(work)]
    if model:
        cmd += ['-m', model]

    if condition == 'skill':
        # Codex reads project skills from .codex/skills/<name>/SKILL.md
        shutil.copytree(BENCH_ROOT / 'conditions' / 'skill' / 'aster', work / '.codex' / 'skills' / 'aster')
        env.update(ASTER_HOME=cfg['aster_home'], ASTER_PYTHON=cfg['python'], ASTER_WORKSPACE=str(work))
    elif condition == 'mcp':
        server = BENCH_ROOT / 'conditions' / 'mcp' / 'aster_mcp_server.py'
        mcp_env = {'ASTER_HOME': cfg['aster_home'], 'ASTER_WORKSPACE': str(work), 'ASTER_LINELISTS': cfg['linelists']}
        cmd += ['-c', f'mcp_servers.aster.command={json.dumps(cfg["python"])}',
                '-c', f'mcp_servers.aster.args={json.dumps([str(server)])}',
                '-c', 'mcp_servers.aster.env={' + ', '.join(f'{k} = {json.dumps(v)}' for k, v in mcp_env.items()) + '}']
    elif condition != 'bare':
        raise ValueError(f"Unknown condition {condition!r}")
    return cmd, env


def parse(transcript: str) -> dict:
    """Best-effort: count tool events and sum any token usage fields in the JSON event stream."""
    stats = {'cost_usd': None, 'input_tokens': 0, 'output_tokens': 0, 'num_turns': None, 'tool_calls': 0,
             'tools_used': {}}
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get('item', {})
        if item.get('type') in ('command_execution', 'mcp_tool_call', 'file_change'):
            if event.get('type') == 'item.completed':
                stats['tool_calls'] += 1
                stats['tools_used'][item['type']] = stats['tools_used'].get(item['type'], 0) + 1
        usage = event.get('usage') or {}
        stats['input_tokens'] += usage.get('input_tokens', 0) or 0
        stats['output_tokens'] += usage.get('output_tokens', 0) or 0
    return stats
