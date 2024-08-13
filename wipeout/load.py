import json
from typing import Annotated

import typer

from wipeout.debugging import load_exception


def main(
    file: Annotated[str, typer.Option("--file", "-f")],
    storage_options_str: Annotated[
        str, typer.Option("--storage-options", "-so")
    ] = "{}",
):
    storage_options: dict = json.loads(storage_options_str)
    load_exception(file, storage_options=storage_options)


if __name__ == "__main__":
    app = typer.Typer(
        add_completion=False,
        context_settings={"help_option_names": ["--help", "-h"]},
    )
    app.command()(main)
    app()
