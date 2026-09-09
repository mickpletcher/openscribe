from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_package_license_notice_includes_runtime_dependencies(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "THIRD-PARTY-LICENSES.txt"

    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "collect-package-licenses.py"), "--output", str(output)],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    notice = output.read_text(encoding="utf-8")
    assert "PySide6 " in notice
    assert "textual " in notice
    assert "typer " in notice
