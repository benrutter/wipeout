import sys
from datetime import datetime
from functools import partial
from typing import Callable

from wipeout.debugging import save_exception_then_raise


def default_filename() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f.wipeout")


def install(
    name_func: Callable[[], str] = default_filename,
    storage_options: dict | None = None,
):
    """
    Override sys.excepthook with customised one, to save error into location first
    """
    storage_options = storage_options or {}
    sys.excepthook = partial(
        save_exception_then_raise, name_func=name_func, storage_options=storage_options
    )
