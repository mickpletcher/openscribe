from __future__ import annotations

from datetime import datetime
import difflib
from io import TextIOWrapper
from pathlib import Path
import shutil
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


def restore_snapshot(root: Path, snapshot_ref: str) -> Path:
    snapshot_dir = _resolve_snapshot(root, snapshot_ref)
    metadata = _load_snapshot_metadata(snapshot_dir)
    mode = str(metadata.get("mode", "")).strip().lower()
    if mode == "checkpoint":
        archive_name = str(metadata.get("archive", "checkpoint.zip"))
        archive_path = snapshot_dir / archive_name
        if not archive_path.exists():
            raise FileNotFoundError(f"Snapshot archive '{archive_path.name}' was not found.")
        with ZipFile(archive_path, "r") as archive:
            archive.extractall(root)
        return snapshot_dir

    if mode == "git":
        commit = str(metadata.get("commit", "")).strip()
        if not commit:
            raise RuntimeError("Git snapshot metadata is missing the commit hash.")
        restore_paths = [
            "manuscript",
            "characters",
            "research",
            "notes",
            ".openscribe/project.yaml",
            ".openscribe/boards",
            ".openscribe/elements",
            ".openscribe/index",
        ]
        result = subprocess.run(
            ["git", "restore", "--source", commit, "--", *restore_paths],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            error_text = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"Git snapshot restore failed. {error_text or 'Unknown git error.'}")
        return snapshot_dir

    raise RuntimeError(f"Unsupported snapshot mode '{mode}'.")


def diff_snapshot(root: Path, snapshot_ref: str) -> str:
    snapshot_dir = _resolve_snapshot(root, snapshot_ref)
    metadata = _load_snapshot_metadata(snapshot_dir)
    mode = str(metadata.get("mode", "")).strip().lower()
    if mode == "git":
        commit = str(metadata.get("commit", "")).strip()
        result = subprocess.run(
            ["git", "diff", "--stat", commit, "--", "manuscript", "characters", "research", "notes", ".openscribe/project.yaml", ".openscribe/boards", ".openscribe/elements"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            error_text = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"Git snapshot diff failed. {error_text or 'Unknown git error.'}")
        return result.stdout.strip() or "[No diff]"

    archive_name = str(metadata.get("archive", "checkpoint.zip"))
    archive_path = snapshot_dir / archive_name
    if not archive_path.exists():
        raise FileNotFoundError(f"Snapshot archive '{archive_path.name}' was not found.")

    current_files = _snapshot_file_map(root)
    snapshot_files = _archive_file_map(archive_path)
    all_paths = sorted(set(current_files) | set(snapshot_files))
    diff_chunks: list[str] = []
    for relative_path in all_paths:
        current_text = current_files.get(relative_path, "").splitlines()
        snapshot_text = snapshot_files.get(relative_path, "").splitlines()
        if current_text == snapshot_text:
            continue
        diff_chunks.append(
            "\n".join(
                difflib.unified_diff(
                    snapshot_text,
                    current_text,
                    fromfile=f"snapshot/{relative_path}",
                    tofile=f"current/{relative_path}",
                    lineterm="",
                )
            )
        )
    return "\n\n".join(chunk for chunk in diff_chunks if chunk.strip()) or "[No diff]"


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


def _resolve_snapshot(root: Path, snapshot_ref: str) -> Path:
    base = snapshots_path(root)
    if not base.exists():
        raise FileNotFoundError("No snapshots exist yet.")
    candidate = base / snapshot_ref
    if candidate.exists():
        return candidate
    for snapshot_dir in base.iterdir():
        if snapshot_dir.name == snapshot_ref or snapshot_ref.lower() in snapshot_dir.name.lower():
            return snapshot_dir
    raise FileNotFoundError(f"Snapshot '{snapshot_ref}' was not found.")


def _load_snapshot_metadata(snapshot_dir: Path) -> dict[str, Any]:
    metadata_path = snapshot_dir / "snapshot.yaml"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Snapshot metadata is missing in '{snapshot_dir.name}'.")
    return yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}


def _snapshot_file_map(root: Path) -> dict[str, str]:
    file_map: dict[str, str] = {}
    include_paths = [
        root / ".openscribe" / "project.yaml",
        root / "manuscript",
        root / "characters",
        root / "research",
        root / "notes",
        root / ".openscribe" / "boards",
        root / ".openscribe" / "elements",
        root / ".openscribe" / "index",
    ]
    for path in include_paths:
        if not path.exists():
            continue
        if path.is_file():
            file_map[str(path.relative_to(root)).replace("\\", "/")] = path.read_text(encoding="utf-8")
            continue
        for child in path.rglob("*"):
            if child.is_file():
                file_map[str(child.relative_to(root)).replace("\\", "/")] = child.read_text(encoding="utf-8")
    return file_map


def _archive_file_map(archive_path: Path) -> dict[str, str]:
    file_map: dict[str, str] = {}
    with ZipFile(archive_path, "r") as archive:
        for name in archive.namelist():
            if name.endswith("/"):
                continue
            with archive.open(name, "r") as handle:
                file_map[name.replace("\\", "/")] = TextIOWrapper(handle, encoding="utf-8").read()
    return file_map
