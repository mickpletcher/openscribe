from __future__ import annotations

import argparse
import os
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path

from openscribe import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="OpenScribe", description="Open the OpenScribe desktop writing application.")
    parser.add_argument("--project", type=Path, help="Project folder to open.")
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--version", action="version", version=f"OpenScribe {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    from openscribe.desktop import AuthorWindow, launch

    if arguments.smoke_test:
        assert AuthorWindow
        import anthropic
        import keyring
        import openai
        from google import genai
        from mistralai.client import Mistral

        assert anthropic and genai and keyring and Mistral and openai
        return 0
    launch(arguments.project)
    return 0


def run(argv: Sequence[str] | None = None) -> int:
    try:
        return main(argv)
    except Exception as exc:  # noqa: BLE001
        local_app_data = os.environ.get("LOCALAPPDATA")
        error_root = Path(local_app_data) / "OpenScribe" if local_app_data else Path.home() / ".openscribe"
        error_path = error_root / "openscribe-error.log"
        try:
            error_root.mkdir(parents=True, exist_ok=True)
            error_path.write_text(traceback.format_exc(), encoding="utf-8")
        except OSError:
            error_path = None
        if "--smoke-test" in (argv if argv is not None else sys.argv[1:]):
            traceback.print_exc()
            return 1
        try:
            import ctypes

            details = f"\n\nDetails: {error_path}" if error_path else ""
            ctypes.windll.user32.MessageBoxW(
                None,
                f"OpenScribe could not start.\n\n{exc}{details}",
                "OpenScribe",
                0x10,
            )
        except (AttributeError, OSError):
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
