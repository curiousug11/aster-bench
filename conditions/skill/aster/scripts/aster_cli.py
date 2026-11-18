"""
Run ASTER tools from the command line, without the orchestral framework.

ASTER's tool classes are written against orchestral's BaseTool/RuntimeField/StateField.
This script installs a minimal stand-in for those names, then instantiates the
requested tool with JSON arguments and calls its _run() method, so all of ASTER's
argument parsing and defaults are preserved.

Usage:
    aster_cli.py list
    aster_cli.py help <Tool>
    aster_cli.py info
    aster_cli.py <Tool> '<json arguments>'

Environment:
    ASTER_HOME       path to the ASTER git clone (default: ~/aster)
    ASTER_WORKSPACE  where outputs are written (default: $ASTER_HOME/workspace)
"""
import importlib
import inspect
import json
import os
import sys
import types
from pathlib import Path

ASTER_HOME = Path(os.environ.get('ASTER_HOME', Path.home() / 'aster')).expanduser().resolve()
WORKSPACE = Path(os.environ.get('ASTER_WORKSPACE', ASTER_HOME / 'workspace')).expanduser().resolve()
PATHS_FILE = WORKSPACE / '.taurex_paths.json'

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
TAUREX_TOOLS = {'RunTaurexTransmissionModelTool', 'RunTaurexEmissionModelTool',
                'SimulateTaurexRetrieval', 'PlotCornerPosteriors'}

_REQUIRED = object()


# --- Minimal stand-in for the orchestral names ASTER imports -------------------------

class _Field:
    def __init__(self, default=_REQUIRED, description='', state=False, **_):
        self.default = default
        self.description = description
        self.state = state


def RuntimeField(**kwargs):
    return _Field(**kwargs)


def StateField(**kwargs):
    return _Field(state=True, **kwargs)


class BaseTool:
    @classmethod
    def fields(cls):
        """Return {name: (annotation, _Field)} for every declared field, base classes first."""
        result = {}
        for klass in reversed(cls.__mro__):
            for name, annotation in vars(klass).get('__annotations__', {}).items():
                value = vars(klass).get(name)
                if isinstance(value, _Field):
                    result[name] = (annotation, value)
        return result

    def __init__(self, **kwargs):
        fields = self.fields()
        unknown = set(kwargs) - set(fields)
        if unknown:
            raise TypeError(f"Unknown argument(s) {sorted(unknown)}. Valid: {sorted(fields)}")
        missing = [n for n, (_, f) in fields.items() if f.default is _REQUIRED and n not in kwargs]
        if missing:
            raise TypeError(f"Missing required argument(s): {missing}")
        for name, (_, field) in fields.items():
            setattr(self, name, kwargs.get(name, field.default))


def define_tool(*_args, **_kwargs):
    return lambda fn: fn


def _install_orchestral_stub():
    modules = {
        'orchestral': {'define_tool': define_tool},
        'orchestral.tools': {},
        'orchestral.tools.base': {},
        'orchestral.tools.base.tool': {'BaseTool': BaseTool},
        'orchestral.tools.base.field_utils': {'RuntimeField': RuntimeField, 'StateField': StateField},
        'orchestral.tools.filesystem': {},
        'orchestral.tools.filesystem.filesystem_tools': {'BaseTool': BaseTool},
    }
    for name, attrs in modules.items():
        module = types.ModuleType(name)
        module.__dict__.update(attrs)
        sys.modules[name] = module


# --- CLI ------------------------------------------------------------------------------

def _load(tool_name):
    if tool_name not in TOOLS:
        sys.exit(f"Unknown tool {tool_name!r}. Run 'list' to see the available tools.")
    _install_orchestral_stub()
    sys.path.insert(0, str(ASTER_HOME))
    return getattr(importlib.import_module(TOOLS[tool_name]), tool_name)


def _saved_taurex_paths():
    if PATHS_FILE.exists():
        return json.loads(PATHS_FILE.read_text())
    linelists = ASTER_HOME / 'workspace' / 'linelists'
    if (linelists / 'xsec').is_dir() and (linelists / 'cia').is_dir():
        return {'opacity_path': str(linelists / 'xsec'), 'cia_path': str(linelists / 'cia')}
    return None


def _apply_taurex_paths():
    paths = _saved_taurex_paths()
    if paths is None:
        print("Warning: no TauREx line-list paths set. Run SetTaurexPaths first.", file=sys.stderr)
        return
    from taurex.cache import OpacityCache, CIACache
    OpacityCache().set_opacity_path(paths['opacity_path'])
    CIACache().set_cia_path(paths['cia_path'])


def cmd_help(tool_name):
    tool = _load(tool_name)
    print(f"{tool_name}\n{inspect.cleandoc(tool.__doc__ or '')}\n\nArguments:")
    if inspect.isfunction(tool):
        for name, param in inspect.signature(tool).parameters.items():
            print(f"  {name} ({param.annotation.__name__}) required")
        return
    for name, (annotation, field) in tool.fields().items():
        if field.state:
            continue  # supplied by this CLI
        kind = 'required' if field.default is _REQUIRED else f"default={field.default!r}"
        type_name = getattr(annotation, '__name__', str(annotation))
        print(f"  {name} ({type_name}) {kind}\n      {field.description}")


def cmd_info():
    print(f"ASTER_HOME:      {ASTER_HOME}")
    print(f"ASTER_WORKSPACE: {WORKSPACE}")
    print(f"Guides:          {ASTER_HOME / 'workspace' / 'skills'}")
    print(f"TauREx paths:    {_saved_taurex_paths()}")


def cmd_run(tool_name, raw_args):
    args = json.loads(raw_args) if raw_args else {}
    tool = _load(tool_name)
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    if tool_name == 'SetTaurexPaths':
        result = tool(**args)
        if result == 'Paths set successfully!':
            PATHS_FILE.write_text(json.dumps(args))  # each CLI call is a new process, so persist
        print(result)
        return

    if tool_name in TAUREX_TOOLS:
        _apply_taurex_paths()
    if 'base_directory' in tool.fields():
        args['base_directory'] = str(WORKSPACE)
    print(tool(**args)._run())


def main(argv):
    if len(argv) < 2 or argv[1] in ('-h', '--help'):
        print(__doc__)
    elif argv[1] == 'list':
        print('\n'.join(TOOLS))
    elif argv[1] == 'info':
        cmd_info()
    elif argv[1] == 'help' and len(argv) > 2:
        cmd_help(argv[2])
    else:
        cmd_run(argv[1], argv[2] if len(argv) > 2 else '')


if __name__ == '__main__':
    main(sys.argv)
