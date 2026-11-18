---
name: aster
description: Exoplanet atmosphere research with the ASTER toolkit. Query the NASA Exoplanet Archive for planet parameters or planets matching conditions, download transit spectra, compute FastChem equilibrium chemistry, run TauREx transmission/emission forward models and atmospheric retrievals, bin spectra to JWST/HST/Ariel instrument resolution, write TauREx .par files for cluster jobs, and make corner plots. Use for any exoplanet spectrum, retrieval, TauREx, FastChem, or exoplanet-archive task.
---

# ASTER (Agentic Science Toolkit for Exoplanet Research)

Every ASTER tool runs through one command, `scripts/aster` in this skill's directory
(normally `~/.claude/skills/aster/scripts/aster`):

```bash
~/.claude/skills/aster/scripts/aster list                 # tool names
~/.claude/skills/aster/scripts/aster help <Tool>          # full description and every argument
~/.claude/skills/aster/scripts/aster info                 # ASTER location, workspace, TauREx paths
~/.claude/skills/aster/scripts/aster <Tool> '<json args>' # run a tool
```

Arguments are one JSON object in single quotes, using native JSON lists/objects, e.g.
`'{"molecules": ["H2O", "CO2"]}'`. Run `help <Tool>` before the first use of a tool in a
session rather than guessing argument names.

All relative file paths (inputs and outputs) are relative to the workspace printed by `info`
(default `$ASTER_HOME/workspace`). Read output files there with the usual file tools; view
generated `.png` plots to check results.

## Tools

| Tool | Use it to |
|---|---|
| `GetExoplanetParameters` | Look up a planet's parameters (`planet_name` like `"WASP-39 b"`, `columns` like `["pl_radj","pl_bmassj","st_rad","pl_eqt"]`) |
| `FindExoplanetsByCondition` | Find planets matching archive conditions (ADQL `conditions`, `return_columns`) |
| `DownloadDataset` | Download archive transit spectra from exactly one of `wget_url` (Firefly wget page), `wget_text`, or `wgets_file_path`; prints the `spectrum.dat` paths to use in retrievals |
| `RunFastChemEquilibriumTool` | Gas-phase equilibrium mixing ratios for a temperature (and optional pressure, `metallicity`, `co_ratio`); no TauREx setup needed |
| `SetTaurexPaths` | Set the TauREx line-list folders (absolute `opacity_path` = `.../linelists/xsec`, `cia_path` = `.../linelists/cia`); saved for later calls |
| `RunTaurexTransmissionModelTool` / `RunTaurexEmissionModelTool` | Forward-model a spectrum (planet radius in RJup, mass in MJup, star radius in Rsun, `planet_temp` in K) |
| `BinSpectrum` | Rebin a spectrum with exactly one of `instrument` (`"list"` shows modes, e.g. `jwst_nirspec_prism`), `resolving_power`, or `n_bins`; output `.dat` is retrieval-ready |
| `SimulateTaurexRetrieval` | Fit an observed spectrum (`observation_path` required); `fit_params`/`bounds` auto-generate if omitted |
| `WriteTaurexParameterFile` | Write a TauREx `.par` file to run on a cluster instead of locally |
| `PlotCornerPosteriors` | Corner plot from retrieval posterior samples |

## Rules (from the ASTER authors)

- **Read the guide first.** Before any retrieval, read `retrieval_best_practices.md`; before TauREx setup or
  FastChem, read `taurex_setup.md` / `fastchem_setup.md`. They are in the Guides folder printed by `info`.
- **TauREx paths:** check `info`. If no paths are shown, check the line lists exist (`ls` the
  `linelists/` folder), then call `SetTaurexPaths` with absolute paths. Never guess paths. If the line lists
  are missing, tell the user to run `python download_linelists.py` in the ASTER folder.
- **Units:** pressures are in Pascals (default atmosphere 1e-1 to 1e6 Pa), not bars.
- **Chemistry:** `chemistry_type` defaults to `free`. Pass `molecular_abundances` only when the user gives
  numbers; pass `molecules` (names only) when they name molecules without numbers. Never invent abundances.
  Use `chemistry_type: "equilibrium"` only if the user asks for equilibrium/ACE chemistry; then do not pass
  `molecules`/`molecular_abundances`. The fit parameter is spelled `C_O_ratio` exactly.
- **Retrieval optimizer:** always pass `optimizer` explicitly; the tool's own default is `multinest`. Use
  `multinest` only if `import pymultinest` works in ASTER's Python, else `nestle`. Use `ultranest` only when
  asked. Molecule bounds are `[1e-12, 1e-2]`, but widen the upper bound (at most `1e-1`) for a species whose
  expected abundance is above 1e-2, such as H2O at 0.02 in the basic forward model. Keep `nlayers` 100.
- **Binning:** forward models are at full line-list resolution (~100k points); bin before plotting or using as
  a synthetic observation. Pass `constant_error` only if the user explicitly asks for it.
- **Binned files as retrieval input:** without `constant_error`, `BinSpectrum` writes 3 columns (wavelength,
  depth, bin width), which a retrieval would misread as (wavelength, depth, error). Also, `constant_error` is
  applied per full-resolution point and then propagated, so the per-bin error comes out much smaller than the
  number given. For a synthetic observation with N ppm per bin, write a 4-column file (wavelength, depth,
  N×1e-6, bin width) from the 3-column output, and tell the user you did so.
- **Long jobs:** retrievals can take many minutes. Run them in the background and check the output when done.
- Planet names use the archive format: `"WASP-39 b"`.

## Common workflows

**Forward model then synthetic observation:** `GetExoplanetParameters` for the planet, then
`RunTaurexTransmissionModelTool` with those values and a `filename`, then `BinSpectrum` on
`<filename>_fm_wavelength.npy` with an `instrument`.

**Retrieval on archive data:** `DownloadDataset` with the user's Firefly wget URL, then read
`retrieval_best_practices.md`, then `SimulateTaurexRetrieval` with the printed `spectrum.dat` path and the
planet's parameters. Outputs: an `.h5` file with full results, `*_fit.png`, `*_corner.png`, posterior `.npy` files.
