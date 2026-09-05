from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote

LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\((?P<target>[^)]+)\)")
HEADING_PATTERN = re.compile(r"^ {0,3}#{1,6}\s+(?P<heading>.+?)\s*#*\s*$")
EXCLUDED_PARTS = {".git", ".pytest_cache", ".ruff_cache", ".venv", "build", "dist"}


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in path.relative_to(root).parts)
    )


def heading_slug(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("`", "").casefold()
    value = "".join(character for character in value if character.isalnum() or character in {" ", "_", "-"})
    return re.sub(r"\s+", "-", value.strip())


def heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    occurrences: dict[str, int] = {}
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_PATTERN.match(line)
        if not match:
            continue
        base = heading_slug(match.group("heading"))
        count = occurrences.get(base, 0)
        anchors.add(base if count == 0 else f"{base}-{count}")
        occurrences[base] = count + 1
    return anchors


def clean_target(value: str) -> str:
    value = value.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    return value.split(maxsplit=1)[0]


def check_links(root: Path) -> tuple[list[str], int, int]:
    issues: list[str] = []
    files = markdown_files(root)
    anchors_by_path: dict[Path, set[str]] = {}
    checked_links = 0
    for source in files:
        in_fence = False
        for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for match in LINK_PATTERN.finditer(line):
                target = clean_target(match.group("target"))
                if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                    continue
                checked_links += 1
                path_text, separator, fragment = target.partition("#")
                target_path = source if not path_text else source.parent / unquote(path_text)
                target_path = target_path.resolve()
                if not target_path.exists():
                    issues.append(f"{source.relative_to(root)}:{line_number}: missing target '{target}'")
                    continue
                if separator and target_path.suffix.casefold() == ".md":
                    anchors = anchors_by_path.setdefault(target_path, heading_anchors(target_path))
                    decoded_fragment = unquote(fragment).casefold()
                    if decoded_fragment not in anchors:
                        issues.append(f"{source.relative_to(root)}:{line_number}: missing heading '#{fragment}' in {path_text or source.name}")
    return issues, len(files), checked_links


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local Markdown targets and heading anchors.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    issues, file_count, link_count = check_links(root)
    if issues:
        for issue in issues:
            print(issue)
        print(f"Found {len(issues)} invalid local links in {file_count} Markdown files.")
        return 1
    print(f"Checked {link_count} local links in {file_count} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
