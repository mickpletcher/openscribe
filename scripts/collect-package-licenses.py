from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def runtime_distributions() -> list:
    pending = ["openscribe", "PySide6"]
    seen: set[str] = set()
    resolved = []
    while pending:
        name = pending.pop()
        normalized = canonicalize_name(name)
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            installed = distribution(name)
        except PackageNotFoundError as exc:
            raise RuntimeError(f"Required distribution is not installed: {name}") from exc
        resolved.append(installed)
        for value in installed.requires or []:
            requirement = Requirement(value)
            if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                continue
            pending.append(requirement.name)
    return sorted(resolved, key=lambda item: canonicalize_name(item.metadata["Name"]))


def license_files(installed) -> list[Path]:
    matches = []
    for item in installed.files or []:
        parts = {part.casefold() for part in item.parts}
        name = item.name.casefold()
        if "licenses" not in parts and not name.startswith(("license", "copying", "notice")):
            continue
        path = Path(installed.locate_file(item))
        if path.is_file():
            matches.append(path)
    return sorted(set(matches), key=lambda item: item.as_posix().casefold())


def build_notice() -> str:
    sections = [
        "OpenScribe third-party licenses",
        "",
        "This file contains license information shipped by the runtime dependencies bundled with OpenScribe.",
    ]
    for installed in runtime_distributions():
        name = installed.metadata["Name"]
        if canonicalize_name(name) == "openscribe":
            continue
        sections.extend(["", "=" * 79, f"{name} {installed.version}", "=" * 79])
        files = license_files(installed)
        if files:
            for path in files:
                sections.extend(["", f"Source file: {path.name}", "", path.read_text(encoding="utf-8", errors="replace").strip()])
        else:
            expression = installed.metadata.get("License-Expression") or installed.metadata.get("License") or "Not declared"
            sections.extend(["", f"Declared license: {expression.strip()}"])
    return "\n".join(sections).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.write_text(build_notice(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
