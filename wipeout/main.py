import sys
import code
from datetime import datetime

import dill
import fsspec
from tblib import pickling_support
from rich import print
from rich.traceback import Traceback


def _gen_name(folder: str):
    name = datetime.now().strftime("%Y%m%d%H%M.pkl")
    return f"{folder}/{name}"

def install(folder=".", storage_options=None, name_generator=_gen_name):
    storage_options = storage_options or {}
    pickling_support.install()
    old_excepthook = sys.excepthook
    def new_hook(type, value, traceback):
        tb_vars = traceback.tb_frame.f_globals | traceback.tb_frame.f_locals
        save_object = {
            "type": type,
            "value": value,
            "traceback": traceback,
            "vars": {
                dill.dumps(k): dill.dumps(v)
                for k, v in tb_vars.items()
            }
        }
        filepath = name_generator(folder)
        with fsspec.open(filepath, 'wb', **storage_options) as file:
            dill.dump(save_object, file)
        print(f"Traceback saved to {filepath}")
        old_excepthook(type, value, traceback)
    sys.excepthook = new_hook


def drop_in(file: str, storage_options=None):
    storage_options = storage_options or {}
    with open(file, 'rb', **storage_options) as f:
        trace_object = dill.load(f)
    print(
        Traceback.from_exception(
            trace_object["type"],
            trace_object["value"],
            trace_object["traceback"],
            extra_lines=20,

        ),
    )
    trace_vars = {}
    errors_loading = False
    for k, v in trace_object["vars"].items():
        try:
            trace_vars[dill.loads(k)] = dill.loads(v)
        except:
            errors_loading = True

    banner = "[bold blue]Crashed Session Loaded[/bold blue]"
    if errors_loading:
        banner += "\nSome variables could not be loaded from session"
    banner += "\nHappy debugging!"
    print(banner)
    code.interact(banner=None, local=trace_vars)
    
