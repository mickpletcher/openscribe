from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def disable_pandoc_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("openscribe.compile.shutil.which", lambda _: None)
