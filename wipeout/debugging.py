import os
import importlib
import sys
import pdb
import pickle
from typing import Callable

from tblib import pickling_support

pickling_support.install()

initial_exception_hook = sys.excepthook


def get_post_mortem():
    """
    Attempts to import the relevant post_mortem function from the PYTHONBREAKPOINT
    environment variable library, in none available (or environment variable not set)
    it will instead return the standard library pdb.post_mortem
    """
    try:
        breakpoint_call: str = os.environ.get("PYTHONBREAKPOINT") or "pdb.set_trace"
        breakpoint_lib, *_ = breakpoint_call.split(".")
        return getattr(
            importlib.import_module(breakpoint_lib),
            "post_mortem",
        )
    except (AttributeError, ModuleNotFoundError):
        return pdb.post_mortem


def save_exception_then_raise(
    type_,
    value,
    traceback,
    name_func: Callable[[], str],
) -> None:
    """
    Gonna overwrite stuff now, cool!
    """
    print("yooooo!")
    with open("error" + name_func(), "wb") as file:
        pickle.dump((type_, value, traceback), file, protocol=pickle.HIGHEST_PROTOCOL)
    GLOBALS = globals()
    to_save_globals = {}
    for key in GLOBALS:
        try:
            pickle.dumps(GLOBALS[key])
            to_save_globals[key] = GLOBALS[key]
        except (pickle.PicklingError, TypeError):
            pass
    with open("global" + name_func(), "wb") as file:
        pickle.dump(to_save_globals, file, protocol=pickle.HIGHEST_PROTOCOL)
    initial_exception_hook(type_, value, traceback)


def load_exception(filename: str):
    with open("error" + filename, "rb") as file:
        type_, value, traceback = pickle.load(file)
    with open("global" + filename, "rb") as file:
        tb_globals = pickle.load(file)
    # setattr(traceback.tb_frame, "f_globals", tb_globals)
    get_post_mortem()(traceback)
