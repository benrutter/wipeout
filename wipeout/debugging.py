import builtins
from contextlib import contextmanager
from pathlib import Path
import os
import sys
import pdb
import gzip
import linecache
from traceback import format_exception
import os
import importlib
import sys
import pdb
import pickle
from typing import Callable

import dill

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
    fake_traceback = FakeTraceback(traceback)
    dump = {
        "traceback": fake_traceback,
    }

    with open("error" + name_func(), "wb") as file:
        dill.dump(dump, file)
    initial_exception_hook(type_, value, traceback)


def load_exception(filename: str):
    with open("error" + filename, "rb") as file:
        dump = dill.load(file)
    get_post_mortem()(dump["traceback"])


class FakeFrame(object):
    def __init__(self, frame):
        self.f_code = FakeCode(frame.f_code)
        self.f_locals = _convert_dict(frame.f_locals)
        self.f_globals = _convert_dict(frame.f_globals)
        self.f_lineno = frame.f_lineno
        self.f_back = FakeFrame(frame.f_back) if frame.f_back else None

        if "self" in self.f_locals:
            self.f_locals["self"] = _convert_obj(frame.f_locals["self"])


class FakeTraceback(object):
    def __init__(self, traceback):
        self.tb_frame = FakeFrame(traceback.tb_frame)
        self.tb_lineno = traceback.tb_lineno
        self.tb_next = FakeTraceback(traceback.tb_next) if traceback.tb_next else None
        self.tb_lasti = 0


class FakeClass(object):
    def __init__(self, repr, vars):
        self.__repr = repr
        self.__dict__.update(vars)

    def __repr__(self):
        return self.__repr


class FakeCode(object):
    def __init__(self, code):
        self.co_filename = os.path.abspath(code.co_filename)
        self.co_name = code.co_name
        self.co_argcount = code.co_argcount
        self.co_consts = tuple(
            FakeCode(c) if hasattr(c, "co_filename") else c for c in code.co_consts
        )
        self.co_firstlineno = code.co_firstlineno
        self.co_lnotab = code.co_lnotab
        self.co_varnames = code.co_varnames
        self.co_flags = code.co_flags
        self.co_code = code.co_code

        # co_lines was introduced in a recent version
        if hasattr(code, "co_lines"):
            self.co_lines = FakeCoLines(code.co_lines)


class FakeCoLines:
    def __init__(self, co_lines) -> None:
        self._co_lines = list(co_lines())

    def __call__(self):
        return iter(self._co_lines)


def _remove_builtins(fake_tb):
    traceback = fake_tb
    while traceback:
        frame = traceback.tb_frame
        while frame:
            frame.f_globals = dict(
                (k, v) for k, v in frame.f_globals.items() if k not in dir(builtins)
            )
            frame = frame.f_back
        traceback = traceback.tb_next


def _inject_builtins(fake_tb):
    traceback = fake_tb
    while traceback:
        frame = traceback.tb_frame
        while frame:
            frame.f_globals.update(builtins.__dict__)
            frame = frame.f_back
        traceback = traceback.tb_next


def _get_traceback_files(traceback):
    files = {}
    while traceback:
        frame = traceback.tb_frame
        while frame:
            filename = os.path.abspath(frame.f_code.co_filename)
            if filename not in files:
                try:
                    files[filename] = open(filename).read()
                except IOError:
                    files[filename] = (
                        "couldn't locate '%s' " "during dump" % frame.f_code.co_filename
                    )
            frame = frame.f_back
        traceback = traceback.tb_next
    return files


def _safe_repr(v):
    try:
        return repr(v)
    except Exception as e:
        return "repr error: " + str(e)


def _convert_obj(obj):
    try:
        return FakeClass(_safe_repr(obj), _convert_dict(obj.__dict__))
    except Exception:
        return _convert(obj)


def _convert_dict(v):
    return dict((_convert(k), _convert(i)) for (k, i) in v.items())


def _convert_seq(v):
    return (_convert(i) for i in v)


def _convert(v):
    if dill is not None:
        try:
            dill.dumps(v)
            return v
        except Exception:
            return _safe_repr(v)
    else:
        from datetime import date, time, datetime, timedelta

        BUILTIN = (str, int, float, date, time, datetime, timedelta)
        # XXX: what about bytes and bytearray?

        if v is None:
            return v

        if type(v) in BUILTIN:
            return v

        if type(v) is tuple:
            return tuple(_convert_seq(v))

        if type(v) is list:
            return list(_convert_seq(v))

        if type(v) is set:
            return set(_convert_seq(v))

        if type(v) is dict:
            return _convert_dict(v)

        return _safe_repr(v)


def _cache_files(files):
    for name, data in files.items():
        lines = [line + "\n" for line in data.splitlines()]
        linecache.cache[name] = (len(data), None, lines, name)


@contextmanager
def add_to_sys_path(path, chdir=False):
    cwd_old = os.getcwd()

    if path is not None:
        path = os.path.abspath(path)
        sys.path.insert(0, path)

        if chdir:
            os.chdir(path)

    try:
        yield
    finally:
        if path is not None:
            sys.path.remove(path)
            os.chdir(cwd_old)
