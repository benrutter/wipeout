import os
import sys
import pdb
import importlib
from typing import Callable

import dill
import fsspec

from .fake_traceback import FakeTraceback

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
    storage_options: dict,
) -> None:
    """
    Exception hook, captures traceback into saveable object
    before outputting file.
    """
    fake_traceback = FakeTraceback(traceback)
    dump = {
        "traceback": fake_traceback,
    }

    with fsspec.open(name_func(), "wb", **storage_options) as file:
        dill.dump(dump, file)
    initial_exception_hook(type_, value, traceback)


def load_exception(filename: str, storage_options: dict):
    """
    Load exception file and enter postmortem
    """
    with fsspec.open(filename, "rb", **storage_options) as file:
        dump = dill.load(file)
    get_post_mortem()(dump["traceback"])
