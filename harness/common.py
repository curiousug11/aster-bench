"""Shared pieces of ASTER-Bench: config, task loading, prompts, work directories."""
import importlib.util
import json
import os
import shutil
from pathlib import Path

import yaml

BENCH_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = BENCH_ROOT / 'tasks'

PREAMBLE = """\
You are working in the current directory. Task inputs are in inputs/. Write all results to outputs/.

Environment:
- Python with TauREx 3, pyfastchem, numpy, astropy and h5py: {python}
- TauREx molecular cross-sections (ExoMol, R=15000, 0.3-50 um): {linelists}/xsec
- TauREx collision-induced absorption files (HITRAN): {linelists}/cia
- FastChem input data (element abundances, logK tables): {fastchem_input}

You cannot ask the user questions, so work autonomously. When you finish, write outputs/answer.json
with the fields requested below. If anything about the inputs or the request is wrong, ambiguous or
impossible, explain it in an "issues" list of strings in answer.json instead of guessing, and use null
for any value you could not determine reliably.

Task:
"""


def load_config():
    """Read bench.yaml (paths to the shared science environment)."""
    path = Path(os.environ.get('ASTER_BENCH_CONFIG', BENCH_ROOT / 'bench.yaml'))
    if not path.exists():
        raise SystemExit(f"Missing {path}. Copy bench.yaml.example to bench.yaml and fill in the paths.")
    cfg = yaml.safe_load(path.read_text())
    for key in ('python', 'aster_home', 'linelists', 'fastchem_input'):
        if key not in cfg:
            raise SystemExit(f"bench.yaml is missing '{key}'")
    return cfg


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Task:
    def __init__(self, task_dir: Path):
        self.dir = task_dir
        self.spec = yaml.safe_load((task_dir / 'task.yaml').read_text())
        self.id = self.spec['id']
        self.tier = self.spec['tier']
        self.timeout_s = int(self.spec.get('timeout_s', 1200))

    def prompt(self, cfg):
        return PREAMBLE.format(**cfg) + self.spec['prompt'].strip() + '\n'

    def module(self, name):
        path = self.dir / f'{name}.py'
        return load_module(path, f'{self.id}_{name}') if path.exists() else None

    def build(self, cfg):
        """Generate inputs/ and hidden/ (synthetic data, reference answers) if the task has a build step."""
        builder = self.module('build')
        if builder and not (self.dir / 'hidden' / '.built').exists():
            (self.dir / 'inputs').mkdir(exist_ok=True)
            (self.dir / 'hidden').mkdir(exist_ok=True)
            builder.build(self.dir, cfg)
            (self.dir / 'hidden' / '.built').write_text('ok')

    def check(self, work: Path) -> dict:
        result = self.module('check').check(work, self.dir / 'hidden')
        result.setdefault('score', 1.0 if result['pass'] else 0.0)
        result.setdefault('notes', '')
        return result


def discover_tasks(pattern='*'):
    dirs = sorted(p.parent for p in TASKS_DIR.glob(f'{pattern}/task.yaml'))
    return [Task(d) for d in dirs]


def make_workdir(task: Task, work: Path):
    """Fresh agent directory with the task inputs and an empty outputs/ folder. Hidden files are never copied."""
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    if (task.dir / 'inputs').exists():
        shutil.copytree(task.dir / 'inputs', work / 'inputs')
    else:
        (work / 'inputs').mkdir()
    (work / 'outputs').mkdir()


# --- Helpers for graders ------------------------------------------------------------------

def load_answer(work: Path):
    path = work / 'outputs' / 'answer.json'
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def issues_text(answer) -> str:
    issues = (answer or {}).get('issues') or []
    if isinstance(issues, str):
        issues = [issues]
    return ' '.join(str(i) for i in issues).lower()


def mentions(text: str, *keyword_groups) -> bool:
    """True if every group has at least one keyword in text. Each group is a tuple of alternatives."""
    return all(any(k in text for k in group) for group in keyword_groups)


def rel_close(value, target, rtol):
    try:
        return abs(float(value) - target) <= rtol * abs(target)
    except (TypeError, ValueError):
        return False


def result(passed, notes='', score=None):
    return {'pass': bool(passed), 'score': (1.0 if passed else 0.0) if score is None else score, 'notes': notes}
