# ASTER-Bench

A benchmark for AI agents doing exoplanet-atmosphere work. It compares **harnesses** (Claude Code, Codex,
…), **models** and **toolsets** (no ASTER, ASTER as a skill, ASTER as an MCP server) on the same tasks, and
grades the results automatically.

General science-agent benchmarks don't test what goes wrong in this field: physical units, telescope data
formats, quietly wrong error bars, and invented abundances. ASTER-Bench focuses on those.

## Conditions

| Condition | What the agent gets |
|---|---|
| `bare` | Python with TauREx, pyfastchem, numpy; line lists; FastChem data. No ASTER. |
| `skill` | The same, plus the ASTER skill (`conditions/skill/aster`), installed per run in the work directory |
| `mcp` | The same, plus ASTER served over MCP (`conditions/mcp/aster_mcp_server.py`) |

Every condition gets the **same prompt** with the same paths. The runners keep your own skills and MCP servers
out of runs. Any `bare` run whose transcript shows ASTER use anyway is marked `contaminated` in `result.json`.

## Tasks (pilot: 8)

| Tier | Task | What it checks |
|---|---|---|
| T2 compute | `t2_scale_height` | Equilibrium temperature, gravity, scale height, one-scale-height signal for a randomised synthetic planet |
| T2 compute | `t2_fastchem_equilibrium` | FastChem at 1100 K, 10x solar: log VMR of H2O, CH4, CO, CO2 within 0.1 dex |
| T3 workflow | `t3_bin_errors` | Bin a high-res model and make a 4-column TauREx observation with 50 ppm per bin |
| T3 workflow | `t3_forward_model` | TauREx transmission model binned to R=50; spectral shape within 15 ppm rms |
| T6 trap | `t6_binwidth_as_error` | A 3-column file whose third column is the bin width, not the error |
| T6 trap | `t6_ppm_units` | Depths given in ppm without saying so |
| T6 trap | `t6_no_abundances` | Asked to use abundances the config doesn't contain |
| T6 trap | `t6_missing_linelist` | HCN requested but there is no HCN cross-section (TauREx silently ignores it) |

Several traps are mistakes we actually hit while testing ASTER. Two of them, `t6_binwidth_as_error` and the
errors in `t3_bin_errors`, are the defaults of ASTER's own `BinSpectrum`. The ASTER skill's `SKILL.md` warns
about those two, so the skill condition gets that knowledge; the bare condition doesn't.

**Not in the pilot yet:** T1 lookup (needs a frozen archive snapshot, because the live archive changes), T4
injection-recovery and T7 compute budgets (need a retrieval setup fast enough to run many times), and T5 real
data (needs the published spectra bundled).

### Task layout

```
tasks/<id>/task.yaml        prompt, tier, timeout
tasks/<id>/build.py         makes inputs/ and hidden/ (synthetic data, true answers); optional
tasks/<id>/check.py         check(work, hidden) -> {pass, score, notes}
tasks/<id>/reference.py     a correct solution; must pass
tasks/<id>/alt_*.py         other correct solutions; must pass (graders must not demand one method)
tasks/<id>/bad_*.py         realistic mistakes; must fail
```

The agent sees only `inputs/` and writes `outputs/answer.json` (plus any files the task asks for). It
reports problems in an `issues` list, which the trap graders read. `hidden/` is never copied into the agent's
directory.

## Running

```bash
env/setup_env.sh /path/to/aster-bench-env      # once: venv, pinned ASTER, ~1.9 GB line lists
cp bench.yaml.example bench.yaml               # fill in the printed paths
PY=/path/to/aster-bench-env/venv/bin/python

$PY -m harness.validate                        # check the graders: references pass, mistakes fail
$PY -m harness.run_matrix --agent claude_code --conditions bare,skill,mcp --seeds 3
$PY -m harness.run_matrix --agent codex --conditions bare,skill,mcp --seeds 3
$PY -m harness.report                          # tables + results/summary.csv
```

`--model` passes a model to the agent CLI, `--tasks 't6_*'` selects tasks, and finished runs are skipped,
so an interrupted matrix resumes. Each run's folder keeps the agent's work directory, `transcript.jsonl`,
`stderr.log` and `result.json`.

## What gets reported

- **pass@1** per tier and overall, averaged over seeds
- **pass^k**: a task counts only if all k seeds pass. Agents vary between runs, so this measures reliability.
- **Cost:** mean $ cost and wall-clock time, tool calls and turns
- **Used ASTER:** fraction of runs that actually called an ASTER tool. Being offered a tool isn't the same as
  using it.
- **Flags:** risky commands (`sudo`, recursive delete of home, `curl | sh`) and contaminated bare runs
- **Harness errors:** runs where the agent never started (bad flags, auth) are marked `harness_error` and
  shown separately, so they aren't counted as agent failures

Use the same model across harnesses where the harnesses allow it, so differences reflect the harness and
toolset rather than the model.

## Status

- **Graders:** all 8 tasks pass `harness.validate` (references and alternatives pass, every bad solution
  fails).
- **Claude Code runner:** smoke-tested on 3 tasks in the bare, skill and MCP conditions (one seed each, about
  $0.15 and 20–50 s per run). Findings:
  - **Bare failed `t2_scale_height`:** it applied the full-redistribution factor twice (T_eq too low by
    1/√2). That's now a `bad_*.py` case.
  - **Traps:** all runs caught the bin-width-as-error and missing-HCN traps.
  - **ASTER wasn't used:** in the skill and MCP runs, the agent was offered ASTER (skill listed, all 11 MCP
    tools connected) but solved every task with its own Python instead. The report's "Used ASTER" column
    tracks this. Without it, skill-vs-bare differences could be mistaken for tool effects when they are
    run-to-run variation.
- **Codex runner** (`runners/codex.py`): written but **not tested**, since Codex wasn't available where this
  was built. Check its flags and JSON event parsing against your Codex version first.
- **Dockerfile:** not built yet; the pilot used `env/setup_env.sh` on the host.
- **Trap grading:** uses keyword matching on `issues`. It's transparent and cheap, but can miss unusual
  wording. Spot-check failed trap runs, or add an LLM judge for T6.
