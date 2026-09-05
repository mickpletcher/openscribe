from __future__ import annotations

import difflib
import os
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

import yaml

from openscribe.locking import project_locked
from openscribe.project import SNAPSHOTS_DIR, slugify
from openscribe.schema import atomic_write_text, load_yaml, validate_snapshot_metadata

MANAGED_PATHS = (
    ".openscribe/project.yaml",
    ".openscribe/templates",
    ".openscribe/boards",
    ".openscribe/elements",
    ".openscribe/index",
    ".openscribe/word-roundtrip",
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


@project_locked
def recover_interrupted_restores(root: Path) -> None:
    transaction_parent = root / ".openscribe"
    if not transaction_parent.exists():
        return
    for transaction_root in sorted(transaction_parent.glob(".restore-transaction-*")):
        _reject_link(transaction_root, boundary=root)
        if not transaction_root.is_dir():
            continue
        journal_path = transaction_root / "journal.yaml"
        if not journal_path.exists():
            _cleanup_restore_transaction(transaction_root)
            continue
        journal = load_yaml(journal_path, default={})
        _validate_journal(journal)
        state = str(journal.get("state", "")).strip().lower()
        if state in {"committed", "rolled_back"}:
            _cleanup_restore_transaction(transaction_root)
            continue
        if state != "applying":
            raise RuntimeError(f"Restore transaction has unknown state '{state}': {journal_path}")
        _rollback_restore_transaction(root, transaction_root, journal)
        journal["state"] = "rolled_back"
        atomic_write_text(journal_path, yaml.safe_dump(journal, sort_keys=False))
        _cleanup_restore_transaction(transaction_root)


@project_locked
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


@project_locked
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


@project_locked
def restore_snapshot(root: Path, snapshot_ref: str) -> RestoreResult:
    recover_interrupted_restores(root)
    snapshot_dir = _resolve_snapshot(root, snapshot_ref)
    metadata = _load_snapshot_metadata(snapshot_dir)
    preview = preview_snapshot_restore(root, snapshot_ref)
    label = str(metadata.get("label", snapshot_dir.name))
    backup_path = create_snapshot(root, f"automatic backup before restoring {label}")
    snapshot_files, present_paths = _snapshot_contents(root, snapshot_dir, metadata)

    try:
        _apply_exact_snapshot(root, snapshot_files, present_paths)
    except Exception as exc:
        recover_interrupted_restores(root)
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
            _reject_link(path, boundary=root)
            if not path.exists():
                continue
            if path.is_file():
                archive.write(path, arcname=relative_path)
                continue
            archive.writestr(relative_path.rstrip("/") + "/", b"")
            for child in path.rglob("*"):
                _reject_link(child, boundary=root)
                if child.is_dir():
                    archive.writestr(child.relative_to(root).as_posix() + "/", b"")
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
        return files, metadata_paths | archive_directories

    if str(metadata.get("mode", "")).strip().lower() == "git":
        commit = str(metadata.get("commit", "")).strip()
        if not commit:
            raise RuntimeError("Git snapshot metadata is missing the commit hash.")
        return _git_file_bytes(root, commit)

    raise FileNotFoundError("Snapshot archive metadata is missing.")


def _archive_file_bytes(archive_path: Path) -> tuple[dict[str, bytes], set[str]]:
    files: dict[str, bytes] = {}
    present_paths: set[str] = set()
    seen: set[str] = set()
    with ZipFile(archive_path, "r") as archive:
        for info in archive.infolist():
            relative_path = _validate_snapshot_relative_path(info.filename)
            normalized = relative_path.rstrip("/").casefold()
            if normalized in seen:
                raise ValueError("Snapshot archive contains duplicate paths.")
            seen.add(normalized)
            managed_path = _managed_parent(relative_path)
            present_paths.add(managed_path)
            if info.is_dir():
                present_paths.add(relative_path.rstrip("/"))
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
        _reject_link(path, boundary=root)
        if not path.exists():
            continue
        if path.is_file():
            files[relative_path] = path.read_bytes()
            continue
        for child in path.rglob("*"):
            _reject_link(child, boundary=root)
            if child.is_file() and not child.is_symlink():
                child_path = str(child.relative_to(root)).replace("\\", "/")
                files[child_path] = child.read_bytes()
    return files


@project_locked
def _apply_exact_snapshot(
    root: Path,
    files: dict[str, bytes],
    present_paths: set[str],
    *,
    paths: tuple[str, ...] = MANAGED_PATHS,
) -> None:
    transaction_root = Path(tempfile.mkdtemp(prefix=".restore-transaction-", dir=root / ".openscribe"))
    stage_root = transaction_root / "stage"
    old_root = transaction_root / "old"
    stage_root.mkdir()
    old_root.mkdir()

    for managed_path in present_paths:
        if not any(managed_path == path or managed_path.startswith(path + "/") for path in paths):
            raise ValueError(f"Snapshot contains unsupported managed path '{managed_path}'.")
        stage_path = stage_root / managed_path
        _validate_snapshot_relative_path(managed_path)
        if managed_path in files:
            stage_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            stage_path.mkdir(parents=True, exist_ok=True)

    for relative_path, content in files.items():
        validated_path = _validate_snapshot_relative_path(relative_path)
        target = stage_root / validated_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    operations: list[dict[str, Any]] = []
    for relative_path in paths:
        _validate_snapshot_relative_path(relative_path)
        target = root / relative_path
        _reject_link(target, boundary=root)
        staged = stage_root / relative_path
        operations.append(
            {
                "path": relative_path,
                "target_existed": target.exists(),
                "staged_existed": staged.exists(),
            }
        )
    journal_path = transaction_root / "journal.yaml"
    journal: dict[str, Any] = {"version": 1, "state": "applying", "operations": operations}
    atomic_write_text(journal_path, yaml.safe_dump(journal, sort_keys=False))
    try:
        for operation in operations:
            relative_path = str(operation["path"])
            target = root / relative_path
            staged = stage_root / relative_path
            old = old_root / relative_path
            if target.exists():
                old.parent.mkdir(parents=True, exist_ok=True)
                target.replace(old)
            if staged.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                staged.replace(target)
        journal["state"] = "committed"
        atomic_write_text(journal_path, yaml.safe_dump(journal, sort_keys=False))
    except Exception:
        _rollback_restore_transaction(root, transaction_root, journal)
        journal["state"] = "rolled_back"
        atomic_write_text(journal_path, yaml.safe_dump(journal, sort_keys=False))
        _cleanup_restore_transaction(transaction_root)
        raise
    _cleanup_restore_transaction(transaction_root)

def _rollback_restore_transaction(root: Path, transaction_root: Path, journal: dict[str, Any]) -> None:
    _validate_journal(journal)
    _reject_link(transaction_root, boundary=root)
    for operation in journal["operations"]:
        for parent in (root, transaction_root / "stage", transaction_root / "old"):
            _reject_link(parent / operation["path"], boundary=root if parent == root else transaction_root)
    operations = journal.get("operations", [])
    if not isinstance(operations, list):
        raise RuntimeError(f"Restore transaction operations are invalid: {transaction_root / 'journal.yaml'}")
    for operation in reversed(operations):
        if not isinstance(operation, dict):
            raise RuntimeError(f"Restore transaction operation is invalid: {transaction_root / 'journal.yaml'}")
        relative_path = str(operation.get("path", ""))
        _validate_snapshot_relative_path(relative_path)
        target = root / relative_path
        staged = transaction_root / "stage" / relative_path
        old = transaction_root / "old" / relative_path
        target_existed = operation.get("target_existed") is True
        staged_existed = operation.get("staged_existed") is True

        if target_existed and old.exists():
            _remove_restore_path(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            old.replace(target)
        elif not target_existed and staged_existed and not staged.exists() and target.exists():
            _remove_restore_path(target)


def _remove_restore_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _cleanup_restore_transaction(transaction_root: Path) -> None:
    def remove_readonly(function, path, _error) -> None:
        os.chmod(path, stat.S_IWRITE)
        function(path)

    try:
        shutil.rmtree(transaction_root, onerror=remove_readonly)
    except OSError:
        return


def _validate_snapshot_relative_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized or path.is_absolute() or ".." in path.parts or ":" in normalized
        or any(part.rstrip(" .") != part for part in path.parts)
        or any(part in {"", ".", ".."} for part in normalized.rstrip("/").split("/"))
    ):
        raise ValueError(f"Unsafe snapshot path '{value}'.")
    _managed_parent(normalized)
    return normalized


def _validate_journal(journal: Any) -> None:
    if not isinstance(journal, dict) or type(journal.get("version")) is not int or journal.get("version") != 1:
        raise RuntimeError("Restore transaction journal has an invalid version or structure.")
    if journal.get("state") not in {"applying", "committed", "rolled_back"}:
        raise RuntimeError("Restore transaction journal has an unknown state.")
    operations = journal.get("operations")
    if not isinstance(operations, list) or not operations:
        raise RuntimeError("Restore transaction operations are invalid.")
    paths: list[str] = []
    for operation in operations:
        if not isinstance(operation, dict) or not isinstance(operation.get("path"), str):
            raise RuntimeError("Restore transaction operation is invalid.")
        path = _validate_snapshot_relative_path(operation["path"]).casefold()
        if any(path == other or path.startswith(other + "/") or other.startswith(path + "/") for other in paths):
            raise RuntimeError("Restore transaction contains duplicate or overlapping paths.")
        paths.append(path)
        if any(type(operation.get(key)) is not bool for key in ("target_existed", "staged_existed")):
            raise RuntimeError("Restore transaction existence fields must be booleans.")


def _reject_link(path: Path, *, boundary: Path) -> None:
    path = path.absolute()
    boundary = boundary.absolute()
    try:
        path.relative_to(boundary)
    except ValueError as exc:
        raise ValueError("Managed project paths must remain under the project root.") from exc
    candidate = path
    while candidate != boundary:
        junction = getattr(candidate, "is_junction", lambda: False)()
        try:
            reparse_tag = getattr(candidate.lstat(), "st_reparse_tag", 0)
        except FileNotFoundError:
            reparse_tag = 0
        if candidate.is_symlink() or junction or reparse_tag in {
            getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003),
            getattr(stat, "IO_REPARSE_TAG_SYMLINK", 0xA000000C),
        }:
            raise ValueError("Managed project paths cannot be symbolic links or junctions.")
        candidate = candidate.parent


def _managed_parent(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").rstrip("/")
    for managed_path in MANAGED_PATHS:
        if normalized == managed_path or normalized.startswith(managed_path.rstrip("/") + "/"):
            return managed_path
    raise ValueError(f"Snapshot path '{relative_path}' is outside the managed project data.")
