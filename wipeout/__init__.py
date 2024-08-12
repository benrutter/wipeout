import sys
from datetime import datetime
from functools import partial
from typing import Callable

from wipeout.debugging import save_exception_then_raise


def default_filename() -> str:
    return datetime.now().strftime("wipeout%Y%m%d%H%M%S%f.pkl")


def install(name_func: Callable[[], str] = default_filename):
    sys.excepthook = partial(save_exception_then_raise, name_func=name_func)
