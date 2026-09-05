from __future__ import annotations

import difflib
import io
import json
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

import yaml
from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring
from docx import Document

from openscribe.editing import EditConflictError, FileEdit, apply_edits, transform_project
from openscribe.index import rebuild_project_index
from openscribe.locking import project_locked
from openscribe.project import (
    SceneDocument,
    _chapter_text,
    _parse_scene_layout,
    _render_scene_layout,
    list_chapters,
    load_project_config,
    parse_frontmatter,
    slugify,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
RT = "urn:openscribe:roundtrip:v1"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
MANIFEST_PART = "customXml/openscribe.xml"
MAX_DOCX_BYTES = 20 * 1024 * 1024
MAX_EXPANDED_BYTES = 80 * 1024 * 1024
ID = re.compile(r"(?:chapter|scene)-[a-f0-9]{32}")


class WordImportError(ValueError):
    pass


def _hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _json(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class WordUnit:
    identity: str
    parent: str | None
    text: str


@dataclass(frozen=True)
class UnitReview:
    identity: str
    status: str
    before: str
    after: str

    @property
    def diff(self) -> str:
        return "\n".join(difflib.unified_diff(
            self.before.splitlines(), self.after.splitlines(), fromfile=f"Markdown/{self.identity}",
            tofile=f"Word/{self.identity}", lineterm="",
        ))


@dataclass(frozen=True)
class WordImportPlan:
    export_id: str
    document_hash: str
    reviews: tuple[UnitReview, ...]
    edits: tuple[FileEdit, ...]
    project_files: dict[str, bytes]
    tracked_changes: int
    warnings: tuple[str, ...]

    @property
    def blocked(self) -> bool:
        return self.tracked_changes > 0 or any(review.status == "conflict" for review in self.reviews)

    @property
    def diff(self) -> str:
        return "\n\n".join(review.diff for review in self.reviews if review.status in {"import", "conflict"})


def _project_units(root: Path) -> tuple[list[WordUnit], dict[str, Path]]:
    units = []
    paths = {}
    for chapter in list_chapters(root):
        if not ID.fullmatch(chapter.chapter_id):
            raise WordImportError("Chapter identity is missing or invalid. Run explicit identity repair first.")
        preamble, scenes = _parse_scene_layout(chapter.body)
        units.append(WordUnit(chapter.chapter_id, None, chapter.title + "\n" + preamble))
        paths[chapter.chapter_id] = chapter.path
        for scene in scenes:
            if not ID.fullmatch(scene.scene_id):
                raise WordImportError("Scene identity is missing or invalid. Run explicit identity repair first.")
            units.append(WordUnit(scene.scene_id, chapter.chapter_id, scene.title + "\n" + scene.body))
    identities = [unit.identity for unit in units]
    if len(identities) != len(set(identities)):
        raise WordImportError("Project contains duplicate identities.")
    return units, paths


def _control(unit: WordUnit) -> ET.Element:
    control = ET.Element(f"{{{W}}}sdt")
    properties = ET.SubElement(control, f"{{{W}}}sdtPr")
    kind = "scene" if unit.parent else "chapter"
    ET.SubElement(properties, f"{{{W}}}tag", {f"{{{W}}}val": f"openscribe:{kind}:{unit.identity}"})
    ET.SubElement(properties, f"{{{W}}}alias", {f"{{{W}}}val": unit.text.split("\n", 1)[0]})
    content = ET.SubElement(control, f"{{{W}}}sdtContent")
    for index, line in enumerate(unit.text.split("\n")):
        paragraph = ET.SubElement(content, f"{{{W}}}p")
        if index == 0:
            props = ET.SubElement(paragraph, f"{{{W}}}pPr")
            ET.SubElement(props, f"{{{W}}}pStyle", {f"{{{W}}}val": "Heading2" if unit.parent else "Heading1"})
        run = ET.SubElement(paragraph, f"{{{W}}}r")
        ET.SubElement(run, f"{{{W}}}t", {"{http://www.w3.org/XML/1998/namespace}space": "preserve"}).text = line
    return control


def _xml(element) -> bytes:
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)


@project_locked
def export_word(root: Path, output: Path) -> Path:
    config = load_project_config(root)
    units, _ = _project_units(root)
    if not units:
        raise WordImportError("Create at least one chapter before exporting a Word round trip.")
    if any(not unit.text.split("\n", 1)[0].strip() for unit in units):
        raise WordImportError("Chapter and scene titles cannot be empty.")
    output = output.resolve()
    if output == root.resolve() or (output.is_relative_to(root.resolve()) and output.parts[len(root.resolve().parts)] != "build"):
        raise WordImportError("Round-trip exports inside a project must be placed under build/.")
    if output.exists():
        raise FileExistsError("Choose a new export filename. Existing Word documents are never overwritten by export.")
    project_id = config.get("project_id", "")
    if not project_id:
        project_id = uuid4().hex
        config_path = root / ".openscribe" / "project.yaml"
        config["project_id"] = project_id
        apply_edits(root, (FileEdit(config_path, config_path.read_bytes(), yaml.safe_dump(config, sort_keys=False).encode()),),
                    "automatic backup before Word project identity")
    if not isinstance(project_id, str) or not re.fullmatch(r"[a-f0-9]{32}", project_id):
        raise WordImportError("Project ID is invalid.")
    export_id = uuid4().hex
    manifest = {
        "version": 1, "export_id": export_id, "project_id": project_id, "project_version": config["version"],
        "exported_at": datetime.now(UTC).isoformat(),
        "units": [{"id": unit.identity, "parent": unit.parent, "hash": _hash(unit.text)} for unit in units],
    }
    baseline = {"manifest": manifest, "texts": {unit.identity: unit.text for unit in units}}
    stream = io.BytesIO()
    Document().save(stream)
    with ZipFile(stream) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    document = fromstring(parts["word/document.xml"])
    body = document.find(f"{{{W}}}body")
    section = body.find(f"{{{W}}}sectPr")
    body.clear()
    controls = {}
    for unit in units:
        control = _control(unit)
        if unit.parent:
            controls[unit.parent].find(f"{{{W}}}sdtContent").append(control)
        else:
            body.append(control)
        controls[unit.identity] = control
    if section is not None:
        body.append(section)
    parts["word/document.xml"] = _xml(document)
    manifest_element = ET.Element(f"{{{RT}}}manifest")
    manifest_element.text = _json(manifest)
    parts[MANIFEST_PART] = _xml(manifest_element)
    relationships = fromstring(parts["word/_rels/document.xml.rels"])
    ET.SubElement(relationships, f"{{{REL}}}Relationship", {
        "Id": "rIdOpenScribe", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml",
        "Target": "../customXml/openscribe.xml",
    })
    parts["word/_rels/document.xml.rels"] = _xml(relationships)
    packaged = io.BytesIO()
    with ZipFile(packaged, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)
    payload = packaged.getvalue()
    parsed_manifest, parsed_units, _, _ = _read_package(payload)
    if parsed_manifest != manifest or parsed_units != units:
        raise WordImportError("Generated Word package did not verify against the export baseline.")
    baseline_path = root / ".openscribe" / "word-roundtrip" / export_id / "baseline.json"
    apply_edits(root, (FileEdit(baseline_path, None, _json(baseline).encode("utf-8")),),
                "automatic backup before Word export baseline")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects an existing document, even if it appeared during export.
    temporary = output.with_name(f".{output.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def _read_package(payload: bytes):
    if len(payload) > MAX_DOCX_BYTES:
        raise WordImportError("Word document exceeds the 20 MiB import limit.")
    try:
        with ZipFile(io.BytesIO(payload)) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)) or len(names) > 5000:
                raise WordImportError("Word package contains duplicate entries or too many parts.")
            if sum(info.file_size for info in infos) > MAX_EXPANDED_BYTES:
                raise WordImportError("Expanded Word package exceeds the size limit.")
            if "word/vbaProject.bin" in names:
                raise WordImportError("Macro-enabled documents are not supported.")
            manifest_root = fromstring(archive.read(MANIFEST_PART))
            if manifest_root.tag != f"{{{RT}}}manifest":
                raise WordImportError("OpenScribe manifest namespace is invalid.")
            manifest = json.loads(manifest_root.text or "")
            document = fromstring(archive.read("word/document.xml"))
            tracked = 0
            for name in names:
                if name.startswith("word/") and name.endswith(".xml"):
                    part = fromstring(archive.read(name))
                    tracked += sum(1 for element in part.iter() if element.tag in {
                        f"{{{W}}}{tag}" for tag in ("ins", "del", "moveFrom", "moveTo", "pPrChange", "rPrChange", "sectPrChange")
                    })
            warnings = ("Word comments are not imported.",) if "word/comments.xml" in names else ()
    except (BadZipFile, KeyError, ET.ParseError, json.JSONDecodeError, DefusedXmlException) as exc:
        raise WordImportError("Word package or OpenScribe manifest is missing or malformed.") from exc
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        raise WordImportError("Unsupported Word manifest version.")
    if not isinstance(manifest.get("export_id"), str) or not re.fullmatch(r"[a-f0-9]{32}", manifest["export_id"]):
        raise WordImportError("Invalid Word export identity.")
    body = document.find(f"{{{W}}}body")
    if body is None:
        raise WordImportError("Word document body is missing.")
    units: list[WordUnit] = []

    def read_control(control, parent=None):
        tag = control.find(f"{{{W}}}sdtPr/{{{W}}}tag")
        value = tag.get(f"{{{W}}}val", "") if tag is not None else ""
        expected_kind = "scene" if parent else "chapter"
        prefix = f"openscribe:{expected_kind}:"
        identity = value.removeprefix(prefix)
        if not value.startswith(prefix) or not re.fullmatch(expected_kind + r"-[a-f0-9]{32}", identity):
            raise WordImportError("Missing, malformed, or incorrectly nested content-control identity.")
        content = control.find(f"{{{W}}}sdtContent")
        if content is None:
            raise WordImportError("Content control has no content.")
        lines = []
        children = []
        for child in content:
            if child.tag == f"{{{W}}}sdt" and parent is None:
                children.append(child)
            elif child.tag == f"{{{W}}}p" and not children:
                unsupported = {f"{{{W}}}{name}" for name in (
                    "sdt", "drawing", "pict", "object", "footnoteReference", "endnoteReference",
                    "fldChar", "instrText", "sym", "altChunk",
                )}
                if any(element.tag in unsupported or "officeDocument/2006/math" in element.tag for element in child.iter()):
                    raise WordImportError("Inline controls, drawings, fields, footnotes, and math cannot be imported safely.")
                parts = []
                for element in child.iter():
                    if element.tag == f"{{{W}}}t":
                        parts.append(element.text or "")
                    elif element.tag in {f"{{{W}}}br", f"{{{W}}}cr"}:
                        parts.append("\n")
                    elif element.tag == f"{{{W}}}tab":
                        parts.append("\t")
                lines.append("".join(parts))
            else:
                raise WordImportError("Unsupported or ambiguous content outside the expected text controls.")
        if not lines or not lines[0].strip():
            raise WordImportError("A chapter or scene title is missing.")
        units.append(WordUnit(identity, parent, "\n".join(lines)))
        for child in children:
            read_control(child, identity)

    for child in body:
        if child.tag == f"{{{W}}}sdt":
            read_control(child)
        elif child.tag != f"{{{W}}}sectPr":
            raise WordImportError("Text outside OpenScribe content controls cannot be mapped safely.")
    identities = [unit.identity for unit in units]
    if len(identities) != len(set(identities)):
        raise WordImportError("Word document contains duplicate content-control IDs.")
    return manifest, units, tracked, warnings


@project_locked
def preview_word_import(root: Path, payload: bytes) -> WordImportPlan:
    from openscribe.snapshots import _current_file_bytes

    config = load_project_config(root)
    manifest, word_units, tracked, warnings = _read_package(payload)
    if manifest.get("project_id") != config.get("project_id"):
        raise WordImportError("This Word document belongs to a different project.")
    baseline_path = root / ".openscribe" / "word-roundtrip" / manifest["export_id"] / "baseline.json"
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise WordImportError("The matching local export baseline is missing or invalid.") from exc
    if not isinstance(baseline, dict) or baseline.get("manifest") != manifest or not isinstance(baseline.get("texts"), dict):
        raise WordImportError("Word manifest does not match the local export baseline.")
    definitions = manifest.get("units")
    actual = [{"id": unit.identity, "parent": unit.parent} for unit in word_units]
    if not isinstance(definitions, list) or any(not isinstance(unit, dict) for unit in definitions):
        raise WordImportError("Invalid manifest unit schema.")
    expected = [{"id": unit.get("id"), "parent": unit.get("parent")} for unit in definitions]
    if actual != expected:
        raise WordImportError("Word controls were added, removed, moved, or have an invalid parent.")
    current_units, paths = _project_units(root)
    current = {unit.identity: unit for unit in current_units}
    if set(current) != {unit.identity for unit in word_units}:
        raise WordImportError("Project structure changed since export. Make a fresh round-trip export.")
    reviews = []
    selected = dict(current)
    for unit, definition in zip(word_units, definitions, strict=True):
        base = baseline["texts"].get(unit.identity)
        if not isinstance(base, str) or _hash(base) != definition.get("hash"):
            raise WordImportError("Local export baseline hash verification failed.")
        markdown = current[unit.identity]
        if markdown.parent != unit.parent:
            raise WordImportError("A scene moved to another chapter after export. Export again before importing.")
        if markdown.text == unit.text:
            status = "unchanged" if unit.text == base else "converged"
        elif unit.text == base:
            status = "keep-markdown"
        elif markdown.text == base:
            status = "import"
            selected[unit.identity] = unit
        else:
            status = "conflict"
        reviews.append(UnitReview(unit.identity, status, markdown.text, unit.text))
    edits = []
    changed = {review.identity for review in reviews if review.status == "import"}
    for chapter in list_chapters(root):
        if not ({chapter.chapter_id, *(scene.scene_id for scene in chapter.scenes)} & changed):
            continue
        before = chapter.path.read_bytes()
        metadata, _ = parse_frontmatter(before.decode("utf-8"))
        title, _, preamble = selected[chapter.chapter_id].text.partition("\n")
        metadata["title"] = title
        scenes = []
        for original in chapter.scenes:
            title, _, body = selected[original.scene_id].text.partition("\n")
            scenes.append(SceneDocument(original.scene_id, title, body, slugify(title)))
        text = _chapter_text(metadata, _render_scene_layout(preamble, scenes))
        edits.append(FileEdit(paths[chapter.chapter_id], before, text.encode("utf-8")))
    return WordImportPlan(manifest["export_id"], sha256(payload).hexdigest(), tuple(reviews), tuple(edits),
                          _current_file_bytes(root), tracked, warnings)


@project_locked
def apply_word_import(root: Path, plan: WordImportPlan) -> Path | None:
    from openscribe.snapshots import _current_file_bytes

    if plan.blocked:
        raise WordImportError("Resolve tracked changes and conflicts before applying this import.")
    if _current_file_bytes(root) != plan.project_files:
        raise EditConflictError("Project changed after the Word preview. Preview again before applying.")
    if not plan.edits:
        return None

    def apply_to_stage(stage: Path):
        for edit in plan.edits:
            target = stage / edit.path.relative_to(root)
            target.write_bytes(edit.after)
        _project_units(stage)
        rebuild_project_index(stage)

    return transform_project(root, "automatic backup before Word round-trip import", apply_to_stage)[0]
