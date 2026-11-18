"""Run Claude Code non-interactively (`claude -p`) on one task in one condition."""
import json
import shutil
from pathlib import Path

from harness.common import BENCH_ROOT

ALLOWED_TOOLS = 'Bash,Read,Write,Edit,Glob,Grep,Skill,TodoWrite,mcp__aster'
PROMPT_VIA_STDIN = True   # --mcp-config takes several values and would swallow a trailing prompt


def prepare(work: Path, condition: str, cfg: dict, model: str | None):
    """Set up the condition inside the work directory and return (command, extra_env)."""
    env = {}
    cmd = ['claude', '-p', '--output-format', 'stream-json', '--verbose',
           '--permission-mode', 'acceptEdits', '--allowedTools', ALLOWED_TOOLS,
           '--strict-mcp-config']  # never load the user's own MCP servers
    if model:
        cmd += ['--model', model]

    if condition == 'skill':
        # Project-level skill, so it only exists for this run
        shutil.copytree(BENCH_ROOT / 'conditions' / 'skill' / 'aster', work / '.claude' / 'skills' / 'aster')
        env.update(ASTER_HOME=cfg['aster_home'], ASTER_PYTHON=cfg['python'], ASTER_WORKSPACE=str(work))
    elif condition == 'mcp':
        mcp_config = {'mcpServers': {'aster': {
            'command': cfg['python'],
            'args': [str(BENCH_ROOT / 'conditions' / 'mcp' / 'aster_mcp_server.py')],
            'env': {'ASTER_HOME': cfg['aster_home'], 'ASTER_WORKSPACE': str(work),
                    'ASTER_LINELISTS': cfg['linelists']},
        }}}
        path = work.parent / 'mcp.json'  # outside work/, so the agent doesn't see harness files
        path.write_text(json.dumps(mcp_config, indent=2))
        cmd += ['--mcp-config', str(path)]
    elif condition != 'bare':
        raise ValueError(f"Unknown condition {condition!r}")
    return cmd, env


def parse(transcript: str) -> dict:
    """Pull cost, tokens, turns and tool calls out of stream-json output."""
    stats = {'cost_usd': None, 'input_tokens': None, 'output_tokens': None, 'num_turns': None, 'tool_calls': 0,
             'tools_used': {}}
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get('type') == 'assistant':
            for block in event.get('message', {}).get('content', []):
                if block.get('type') == 'tool_use':
                    stats['tool_calls'] += 1
                    name = block.get('name', '?')
                    stats['tools_used'][name] = stats['tools_used'].get(name, 0) + 1
        elif event.get('type') == 'result':
            usage = event.get('usage', {})
            stats.update(cost_usd=event.get('total_cost_usd'), num_turns=event.get('num_turns'),
                         input_tokens=(usage.get('input_tokens', 0) + usage.get('cache_read_input_tokens', 0)
                                       + usage.get('cache_creation_input_tokens', 0)),
                         output_tokens=usage.get('output_tokens'))
    return stats
