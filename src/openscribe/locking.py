from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

_guard = threading.Lock()
_locks: dict[Path, threading.RLock] = {}
_held = threading.local()


class ProjectBusyError(RuntimeError):
    pass


@contextmanager
def project_lock(root: Path):
    root = root.resolve()
    with _guard:
        lock = _locks.setdefault(root, threading.RLock())
    with lock:
        held = getattr(_held, "roots", set())
        if root in held:
            yield
            return
        directory = root / ".openscribe"
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("Project metadata directory is missing or is a symbolic link.")
        lock_path = directory / ".write.lock"
        if lock_path.is_symlink():
            raise ValueError("Project lock cannot be a symbolic link.")
        with lock_path.open("a+b") as handle:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise ProjectBusyError("Another OpenScribe process is using this project. Retry after it finishes.") from exc
            _held.roots = held | {root}
            try:
                yield
            finally:
                _held.roots = held
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)


def project_locked(function):
    @wraps(function)
    def locked(root: Path, *args, **kwargs):
        with project_lock(root):
            return function(root, *args, **kwargs)

    return locked
