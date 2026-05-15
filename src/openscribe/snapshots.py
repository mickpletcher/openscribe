from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

import yaml

from openscribe.project import SNAPSHOTS_DIR, slugify


def snapshots_path(root: Path) -> Path:
    return root / SNAPSHOTS_DIR


def create_snapshot(root: Path, label: str, mode: str = "checkpoint") -> Path:
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"checkpoint", "git"}:
        raise ValueError("Snapshot mode must be checkpoint or git.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot_slug = slugify(label)
    snapshot_dir = snapshots_path(root) / f"{timestamp}-{snapshot_slug}"
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    metadata: dict[str, Any] = {
        "label": label,
        "mode": normalized_mode,
        "created_at": timestamp,
    }

    if normalized_mode == "git":
        metadata.update(_git_snapshot_metadata(root))
        (snapshot_dir / "snapshot.yaml").write_text(
            yaml.safe_dump(metadata, sort_keys=False),
            encoding="utf-8",
        )
        return snapshot_dir

    archive_path = snapshot_dir / "checkpoint.zip"
    _write_checkpoint_archive(root, archive_path)
    metadata["archive"] = archive_path.name
    (snapshot_dir / "snapshot.yaml").write_text(
        yaml.safe_dump(metadata, sort_keys=False),
        encoding="utf-8",
    )
    return snapshot_dir


def list_snapshots(root: Path) -> list[dict[str, Any]]:
    base = snapshots_path(root)
    if not base.exists():
        return []

    records: list[dict[str, Any]] = []
    for snapshot_dir in sorted([path for path in base.iterdir() if path.is_dir()], reverse=True):
        metadata_path = snapshot_dir / "snapshot.yaml"
        if not metadata_path.exists():
            continue
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
        metadata["path"] = str(snapshot_dir.relative_to(root))
        records.append(metadata)
    return records


def _git_snapshot_metadata(root: Path) -> dict[str, Any]:
    commit_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if commit_result.returncode != 0:
        raise RuntimeError("Git snapshot mode requires a git repository with at least one commit.")

    status_result = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "commit": commit_result.stdout.strip(),
        "dirty": bool(status_result.stdout.strip()),
        "status": status_result.stdout.strip().splitlines(),
    }


def _write_checkpoint_archive(root: Path, archive_path: Path) -> None:
    include_paths = [
        root / ".openscribe" / "project.yaml",
        root / "manuscript",
        root / "characters",
        root / "research",
        root / "notes",
    ]
    optional_paths = [
        root / ".openscribe" / "boards",
        root / ".openscribe" / "elements",
        root / ".openscribe" / "index",
    ]

    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in [*include_paths, *optional_paths]:
            if not path.exists():
                continue
            if path.is_file():
                archive.write(path, arcname=str(path.relative_to(root)))
                continue
            for child in path.rglob("*"):
                if child.is_file():
                    archive.write(child, arcname=str(child.relative_to(root)))
