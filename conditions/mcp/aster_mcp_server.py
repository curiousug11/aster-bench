"""
Serve the ASTER toolkit to Claude Code (or any MCP client) over stdio.

Environment:
    ASTER_HOME       path to the ASTER git clone (required)
    ASTER_WORKSPACE  where outputs are written (default: $ASTER_HOME/workspace)
    ASTER_LINELISTS  folder with xsec/ and cia/ (optional; sets TauREx paths at startup)
"""
import contextlib
import importlib
import os
import sys
from pathlib import Path

ROOT = Path(os.environ['ASTER_HOME']).resolve()
sys.path.insert(0, str(ROOT))

# Same tool set as the ASTER skill, so the two conditions are comparable
TOOLS = {
    'GetExoplanetParameters': 'aster_toolkit.data_acquisition.exoarchive',
    'FindExoplanetsByCondition': 'aster_toolkit.data_acquisition.exoarchive',
    'DownloadDataset': 'aster_toolkit.data_acquisition.exoarchive',
    'SetTaurexPaths': 'aster_toolkit.taurex.set_paths',
    'RunTaurexTransmissionModelTool': 'aster_toolkit.taurex.forward_model',
    'RunTaurexEmissionModelTool': 'aster_toolkit.taurex.forward_model',
    'SimulateTaurexRetrieval': 'aster_toolkit.taurex.retrieval',
    'WriteTaurexParameterFile': 'aster_toolkit.taurex.parfile_tools',
    'PlotCornerPosteriors': 'aster_toolkit.taurex.corner_plot',
    'RunFastChemEquilibriumTool': 'aster_toolkit.chemistry.fastchem_tools',
    'BinSpectrum': 'aster_toolkit.binning_tool.bin_spectrum_tool',
}

# stdout is the MCP channel, so keep any import-time chatter off it.
with contextlib.redirect_stdout(sys.stderr):
    from orchestral.mcp import MCPServer
    tool_objects = {name: getattr(importlib.import_module(module), name) for name, module in TOOLS.items()}

base_directory = os.environ.get('ASTER_WORKSPACE', str(ROOT / 'workspace'))
os.makedirs(base_directory, exist_ok=True)
os.chdir(base_directory)

linelists = os.environ.get('ASTER_LINELISTS')
if linelists:
    from taurex.cache import OpacityCache, CIACache
    with contextlib.redirect_stdout(sys.stderr):
        OpacityCache().set_opacity_path(str(Path(linelists) / 'xsec'))
        CIACache().set_cia_path(str(Path(linelists) / 'cia'))

tools = []
for name, obj in tool_objects.items():
    if isinstance(obj, type):
        # Only pass base_directory to tools that declare it as a StateField
        kwargs = {'base_directory': base_directory} if 'base_directory' in obj._get_state_fields() else {}
        obj = obj(**kwargs)
    # Advertise the class name (e.g. GetExoplanetParameters) instead of orchestral's lowercased default
    obj._mcp_display_name = name.removesuffix('Tool')
    tools.append(obj)

instructions = f"""ASTER: tools for exoplanet atmosphere research (NASA Exoplanet Archive, TauREx, FastChem).
All tool outputs are written under {base_directory}; relative paths resolve there.
Before running TauREx models or retrievals, read the guides in {ROOT / 'workspace' / 'skills'}
(taurex_setup.md, retrieval_best_practices.md, fastchem_setup.md, corner_plots.md).
SetTaurexPaths needs absolute paths to the xsec/ and cia/ folders. Pressures are in Pascals."""

if __name__ == '__main__':
    MCPServer(tools=tools, name='aster', instructions=instructions).run()
