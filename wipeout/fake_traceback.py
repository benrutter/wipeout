import os

import dill


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
    try:
        dill.dumps(v)
        return v
    except Exception:
        return _safe_repr(v)
