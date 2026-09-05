from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_markdown_links.py"


def run_checker(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        capture_output=True,
        check=False,
        text=True,
    )


def test_markdown_checker_accepts_local_files_and_headings(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("# Guide\n\n## First step\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("[Guide](guide.md#first-step)\n", encoding="utf-8")

    result = run_checker(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Checked 1 local links in 2 Markdown files." in result.stdout


def test_markdown_checker_rejects_missing_file(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("[Missing](missing.md)\n", encoding="utf-8")

    result = run_checker(tmp_path)

    assert result.returncode == 1
    assert "missing target 'missing.md'" in result.stdout


def test_markdown_checker_rejects_missing_heading(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("# Guide\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("[Missing heading](guide.md#not-here)\n", encoding="utf-8")

    result = run_checker(tmp_path)

    assert result.returncode == 1
    assert "missing heading '#not-here'" in result.stdout
