from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from openscribe.locking import project_lock
from openscribe.project import create_chapter, create_part, init_project, load_project_config
from openscribe.snapshots import _current_file_bytes, create_snapshot, restore_snapshot


@pytest.mark.parametrize("boundary", ["old", "new"])
def test_terminated_restore_recovers_exactly_and_only_once(tmp_path: Path, boundary):
    root = init_project(tmp_path, "Process recovery")
    create_part(root, "Opening")
    chapter = create_chapter(root, "Arrival")
    chapter.write_bytes(chapter.read_bytes() + b"Checkpoint text.")
    snapshot = create_snapshot(root, "checkpoint")
    chapter.write_bytes(chapter.read_bytes() + b" New current text.")
    before = _current_file_bytes(root)
    code = '''
import os, sys
from pathlib import Path
from openscribe.snapshots import restore_snapshot
root, reference, boundary = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
real_replace = Path.replace
def terminate(path, target):
    result = real_replace(path, target)
    if boundary == 'old' and path == root / 'manuscript':
        os._exit(91)
    if boundary == 'new' and 'stage' in path.parts and target == root / 'manuscript':
        os._exit(91)
    return result
Path.replace = terminate
restore_snapshot(root, reference)
'''
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parents[1] / "src"))
    result = subprocess.run([sys.executable, "-c", code, str(root), snapshot.name, boundary],
                            env=environment, capture_output=True, timeout=30, check=False)
    assert result.returncode == 91, result.stderr.decode()
    load_project_config(root)
    assert _current_file_bytes(root) == before
    later = root / "notes" / "later.md"
    later.write_text("Later work", encoding="utf-8")
    load_project_config(root)
    assert later.read_text(encoding="utf-8") == "Later work"


def test_other_process_cannot_enter_a_live_transaction(tmp_path):
    root = init_project(tmp_path, "Lock test")
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parents[1] / "src"))
    code = "from pathlib import Path; from openscribe.project import load_project_config; import sys; load_project_config(Path(sys.argv[1]))"
    with project_lock(root):
        result = subprocess.run([sys.executable, "-c", code, str(root)], env=environment,
                                capture_output=True, timeout=30, check=False)
    assert result.returncode != 0
    assert b"Another OpenScribe process" in result.stderr
    assert load_project_config(root)["title"] == "Lock test"


def test_restore_preserves_empty_nested_directories(tmp_path):
    root = init_project(tmp_path, "Directory restore")
    empty = root / "research" / "empty" / "nested"
    empty.mkdir(parents=True)
    snapshot = create_snapshot(root, "empty directories")
    (root / "research" / "extra.md").write_text("Later", encoding="utf-8")
    restore_snapshot(root, snapshot.name)
    assert empty.is_dir()
    assert not (root / "research" / "extra.md").exists()
