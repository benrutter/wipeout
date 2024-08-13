import sys
import runpy
import rich
from typing import Annotated

import typer

from wipeout.debugging import get_post_mortem


def main(
    script: Annotated[str, typer.Option("--script", "-s")],
):
    if len(sys.argv) < 2:
        print("Usage: python -m wipeout.run my/script.py")
        sys.exit(1)
    script_name = sys.argv[1]

    try:
        runpy.run_path(script_name, run_name="__main__")
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        rich.print("[u red]Exception raised, entering debugger[/u red]")
        rich.print(f"{exc_type}: {exc_value}\n\n")
        get_post_mortem()(exc_traceback)


if __name__ == "__main__":
    app = typer.Typer(
        add_completion=False,
        context_settings={"help_option_names": ["--help", "-h"]},
    )
    app.command()(main)
    app()
