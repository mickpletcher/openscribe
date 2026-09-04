from __future__ import annotations

import difflib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

import yaml

from openscribe.project import SNAPSHOTS_DIR, slugify
from openscribe.schema import atomic_write_text, load_yaml, validate_snapshot_metadata

MANAGED_PATHS = (
    ".openscribe/project.yaml",
    ".openscribe/templates",
    ".openscribe/boards",
    ".openscribe/elements",
    ".openscribe/index",
    "manuscript",
    "characters",
    "research",
    "notes",
)


@dataclass(frozen=True, slots=True)
class RestorePreview:
    snapshot_path: Path
    added: tuple[str, ...]
    modified: tuple[str, ...]
    deleted: tuple[str, ...]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.modified or self.deleted)


@dataclass(frozen=True, slots=True)
class RestoreResult:
    snapshot_path: Path
    backup_path: Path
    preview: RestorePreview


def snapshots_path(root: Path) -> Path:
    return root / SNAPSHOTS_DIR


def create_snapshot(root: Path, label: str, mode: str = "checkpoint") -> Path:
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"checkpoint", "git"}:
        raise ValueError("Snapshot mode must be checkpoint or git.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    snapshot_slug = slugify(label)
    snapshot_dir = snapshots_path(root) / f"{timestamp}-{snapshot_slug}"
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    metadata: dict[str, Any] = {
        "label": label,
        "mode": normalized_mode,
        "created_at": timestamp,
        "managed_paths": [path for path in MANAGED_PATHS if (root / path).exists()],
    }

    try:
        if normalized_mode == "git":
            metadata.update(_git_snapshot_metadata(root))

        archive_path = snapshot_dir / "checkpoint.zip"
        _write_checkpoint_archive(root, archive_path)
        metadata["archive"] = archive_path.name
        atomic_write_text(
            snapshot_dir / "snapshot.yaml",
            yaml.safe_dump(metadata, sort_keys=False),
        )
    except Exception:
        shutil.rmtree(snapshot_dir)
        raise
    return snapshot_dir


def list_snapshots(root: Path) -> list[dict[str, Any]]:
    base = snapshots_path(root)
    if not base.exists():
        return []

    records: list[dict[str, Any]] = []
    for snapshot_dir in sorted((path for path in base.iterdir() if path.is_dir()), reverse=True):
        metadata_path = snapshot_dir / "snapshot.yaml"
        if not metadata_path.exists():
            continue
        metadata = validate_snapshot_metadata(
            load_yaml(metadata_path, default={}),
            f"Snapshot metadata '{metadata_path}'",
        )
        metadata["path"] = str(snapshot_dir.relative_to(root))
        records.append(metadata)
    return records


def preview_snapshot_restore(root: Path, snapshot_ref: str) -> RestorePreview:
    snapshot_dir = _resolve_snapshot(root, snapshot_ref)
    metadata = _load_snapshot_metadata(snapshot_dir)
    snapshot_files, _ = _snapshot_contents(root, snapshot_dir, metadata)
    current_files = _current_file_bytes(root)
    snapshot_names = set(snapshot_files)
    current_names = set(current_files)
    return RestorePreview(
        snapshot_path=snapshot_dir,
        added=tuple(sorted(snapshot_names - current_names)),
        modified=tuple(
            sorted(path for path in snapshot_names & current_names if snapshot_files[path] != current_files[path])
        ),
        deleted=tuple(sorted(current_names - snapshot_names)),
    )


def restore_snapshot(root: Path, snapshot_ref: str) -> RestoreResult:
    snapshot_dir = _resolve_snapshot(root, snapshot_ref)
    metadata = _load_snapshot_metadata(snapshot_dir)
    preview = preview_snapshot_restore(root, snapshot_ref)
    label = str(metadata.get("label", snapshot_dir.name))
    backup_path = create_snapshot(root, f"automatic backup before restoring {label}")
    snapshot_files, present_paths = _snapshot_contents(root, snapshot_dir, metadata)

    try:
        _apply_exact_snapshot(root, snapshot_files, present_paths)
    except Exception as exc:
        backup_metadata = _load_snapshot_metadata(backup_path)
        backup_files, backup_present_paths = _snapshot_contents(root, backup_path, backup_metadata)
        try:
            _apply_exact_snapshot(root, backup_files, backup_present_paths)
        except Exception as rollback_exc:
            raise RuntimeError(
                f"Snapshot restore failed and rollback also failed. Backup: {backup_path}. "
                f"Restore error: {exc}. Rollback error: {rollback_exc}."
            ) from rollback_exc
        raise RuntimeError(
            f"Snapshot restore failed and the automatic backup was restored. Backup: {backup_path}. {exc}"
        ) from exc

    return RestoreResult(snapshot_path=snapshot_dir, backup_path=backup_path, preview=preview)


def diff_snapshot(root: Path, snapshot_ref: str) -> str:
    snapshot_dir = _resolve_snapshot(root, snapshot_ref)
    metadata = _load_snapshot_metadata(snapshot_dir)
    snapshot_files, _ = _snapshot_contents(root, snapshot_dir, metadata)
    current_files = _current_file_bytes(root)
    all_paths = sorted(set(current_files) | set(snapshot_files))
    diff_chunks: list[str] = []
    for relative_path in all_paths:
        current_bytes = current_files.get(relative_path, b"")
        snapshot_bytes = snapshot_files.get(relative_path, b"")
        if current_bytes == snapshot_bytes:
            continue
        try:
            current_text = current_bytes.decode("utf-8").splitlines()
            snapshot_text = snapshot_bytes.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            diff_chunks.append(f"Binary file changed: {relative_path}")
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
    if status_result.returncode != 0:
        raise RuntimeError("Git snapshot mode could not read the repository status.")
    return {
        "commit": commit_result.stdout.strip(),
        "dirty": bool(status_result.stdout.strip()),
        "status": status_result.stdout.strip().splitlines(),
    }


def _write_checkpoint_archive(root: Path, archive_path: Path) -> None:
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for relative_path in MANAGED_PATHS:
            path = root / relative_path
            if not path.exists():
                continue
            if path.is_file():
                archive.write(path, arcname=relative_path)
                continue
            archive.writestr(relative_path.rstrip("/") + "/", b"")
            for child in path.rglob("*"):
                if child.is_file() and not child.is_symlink():
                    archive.write(
                        child,
                        arcname=str(child.relative_to(root)).replace("\\", "/"),
                    )


def _resolve_snapshot(root: Path, snapshot_ref: str) -> Path:
    base = snapshots_path(root).resolve()
    if not base.exists():
        raise FileNotFoundError("No snapshots exist yet.")

    candidate = (base / snapshot_ref).resolve()
    if candidate.is_relative_to(base) and candidate.is_dir():
        return candidate

    matches = [path for path in base.iterdir() if path.is_dir() and snapshot_ref.lower() in path.name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise FileNotFoundError(f"Snapshot reference '{snapshot_ref}' is ambiguous.")
    raise FileNotFoundError(f"Snapshot '{snapshot_ref}' was not found.")


def _load_snapshot_metadata(snapshot_dir: Path) -> dict[str, Any]:
    metadata_path = snapshot_dir / "snapshot.yaml"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Snapshot metadata is missing in '{snapshot_dir.name}'.")
    return validate_snapshot_metadata(
        load_yaml(metadata_path, default={}),
        f"Snapshot metadata '{metadata_path}'",
    )


def _snapshot_contents(
    root: Path,
    snapshot_dir: Path,
    metadata: dict[str, Any],
) -> tuple[dict[str, bytes], set[str]]:
    archive_name = str(metadata.get("archive", "")).strip()
    if archive_name:
        archive_path = (snapshot_dir / archive_name).resolve()
        if not archive_path.is_relative_to(snapshot_dir.resolve()):
            raise ValueError("Snapshot archive path leaves the snapshot directory.")
        if not archive_path.exists():
            raise FileNotFoundError(f"Snapshot archive '{archive_path.name}' was not found.")
        files, archive_directories = _archive_file_bytes(archive_path)
        metadata_paths = {str(path) for path in metadata.get("managed_paths", []) if str(path) in MANAGED_PATHS}
        return files, metadata_paths or archive_directories

    if str(metadata.get("mode", "")).strip().lower() == "git":
        commit = str(metadata.get("commit", "")).strip()
        if not commit:
            raise RuntimeError("Git snapshot metadata is missing the commit hash.")
        return _git_file_bytes(root, commit)

    raise FileNotFoundError("Snapshot archive metadata is missing.")


def _archive_file_bytes(archive_path: Path) -> tuple[dict[str, bytes], set[str]]:
    files: dict[str, bytes] = {}
    present_paths: set[str] = set()
    with ZipFile(archive_path, "r") as archive:
        for info in archive.infolist():
            relative_path = _validate_snapshot_relative_path(info.filename)
            managed_path = _managed_parent(relative_path)
            present_paths.add(managed_path)
            if info.is_dir():
                continue
            files[relative_path] = archive.read(info)
    return files, present_paths


def _git_file_bytes(root: Path, commit: str) -> tuple[dict[str, bytes], set[str]]:
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "-z", commit, "--", *MANAGED_PATHS],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if listing.returncode != 0:
        raise RuntimeError("Git snapshot restore could not list files from the recorded commit.")

    files: dict[str, bytes] = {}
    present_paths: set[str] = set()
    for raw_name in listing.stdout.split(b"\0"):
        if not raw_name:
            continue
        relative_path = _validate_snapshot_relative_path(raw_name.decode("utf-8"))
        content = subprocess.run(
            ["git", "show", f"{commit}:{relative_path}"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if content.returncode != 0:
            raise RuntimeError(f"Git snapshot restore could not read '{relative_path}'.")
        files[relative_path] = content.stdout
        present_paths.add(_managed_parent(relative_path))
    return files, present_paths


def _current_file_bytes(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for relative_path in MANAGED_PATHS:
        path = root / relative_path
        if not path.exists():
            continue
        if path.is_file():
            files[relative_path] = path.read_bytes()
            continue
        for child in path.rglob("*"):
            if child.is_file() and not child.is_symlink():
                child_path = str(child.relative_to(root)).replace("\\", "/")
                files[child_path] = child.read_bytes()
    return files


def _apply_exact_snapshot(
    root: Path,
    files: dict[str, bytes],
    present_paths: set[str],
) -> None:
    transaction_root = Path(tempfile.mkdtemp(prefix=".restore-transaction-", dir=root / ".openscribe"))
    stage_root = transaction_root / "stage"
    old_root = transaction_root / "old"
    stage_root.mkdir()
    old_root.mkdir()

    for managed_path in present_paths:
        if managed_path not in MANAGED_PATHS:
            raise ValueError(f"Snapshot contains unsupported managed path '{managed_path}'.")
        stage_path = stage_root / managed_path
        if managed_path == ".openscribe/project.yaml":
            stage_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            stage_path.mkdir(parents=True, exist_ok=True)

    for relative_path, content in files.items():
        validated_path = _validate_snapshot_relative_path(relative_path)
        target = stage_root / validated_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    operations: list[dict[str, Any]] = []
    try:
        for relative_path in MANAGED_PATHS:
            target = root / relative_path
            staged = stage_root / relative_path
            old = old_root / relative_path
            operation = {
                "target": target,
                "staged": staged,
                "old": old,
                "moved_old": False,
                "installed": False,
            }
            operations.append(operation)
            if target.exists():
                old.parent.mkdir(parents=True, exist_ok=True)
                target.replace(old)
                operation["moved_old"] = True
            if staged.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                staged.replace(target)
                operation["installed"] = True
    except Exception:
        for operation in reversed(operations):
            target = operation["target"]
            staged = operation["staged"]
            old = operation["old"]
            if operation["installed"] and target.exists():
                staged.parent.mkdir(parents=True, exist_ok=True)
                target.replace(staged)
            if operation["moved_old"] and old.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                old.replace(target)
        raise
    finally:
        shutil.rmtree(transaction_root, ignore_errors=True)

    for directory in ("manuscript", "characters", "research", "notes"):
        (root / directory).mkdir(parents=True, exist_ok=True)


def _validate_snapshot_relative_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip("/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe snapshot path '{value}'.")
    _managed_parent(normalized)
    return normalized


def _managed_parent(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").rstrip("/")
    for managed_path in MANAGED_PATHS:
        if normalized == managed_path or normalized.startswith(managed_path.rstrip("/") + "/"):
            return managed_path
    raise ValueError(f"Snapshot path '{relative_path}' is outside the managed project data.")
