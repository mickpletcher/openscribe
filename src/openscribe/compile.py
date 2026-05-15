from __future__ import annotations

from html import escape
from pathlib import Path

from docx import Document
from ebooklib import epub
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from openscribe.project import ChapterDocument, list_chapters, load_project_config, slugify


class CompileError(RuntimeError):
    pass


def compile_project(root: Path, format_name: str | None = None, output_path: Path | None = None) -> Path:
    config = load_project_config(root)
    project_title = str(config.get("title", "Untitled Project"))
    compile_format = _resolve_format(config, format_name, output_path)
    chapters = _compiled_chapters(root)
    target_path = output_path or default_output_path(root, project_title, compile_format)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if compile_format == "docx":
        _compile_project_to_docx(project_title, str(config.get("author", "")).strip(), chapters, target_path)
        return target_path
    if compile_format == "pdf":
        _compile_project_to_pdf(project_title, str(config.get("author", "")).strip(), chapters, target_path)
        return target_path
    if compile_format == "epub":
        _compile_project_to_epub(project_title, str(config.get("author", "")).strip(), chapters, target_path)
        return target_path

    raise CompileError(
        f"Format '{compile_format}' is not supported yet. Use docx, pdf, or epub."
    )


def default_output_path(root: Path, project_title: str, compile_format: str) -> Path:
    return root / "build" / f"{slugify(project_title)}.{compile_format}"


def _resolve_format(config: dict, format_name: str | None, output_path: Path | None) -> str:
    if format_name:
        return format_name.strip().lower()
    if output_path and output_path.suffix:
        return output_path.suffix.lstrip(".").lower()
    compile_config = config.get("compile", {})
    return str(compile_config.get("default_format", "docx")).lower()


def _compiled_chapters(root: Path) -> list[ChapterDocument]:
    chapters = list_chapters(root)
    if not chapters:
        raise CompileError("No manuscript content exists yet. Create at least one chapter first.")

    populated_chapters = [chapter for chapter in chapters if chapter.body.strip()]
    if not populated_chapters:
        raise CompileError("No manuscript body text exists yet. Add text to at least one chapter first.")
    return populated_chapters


def _compile_project_to_docx(
    project_title: str,
    author: str,
    chapters: list[ChapterDocument],
    target_path: Path,
) -> None:
    document = Document()
    document.core_properties.title = project_title
    if author:
        document.core_properties.author = author

    document.add_heading(project_title, level=0)
    if author:
        document.add_paragraph(author)

    current_part = None
    for chapter in chapters:
        if chapter.part_id != current_part:
            current_part = chapter.part_id
            document.add_page_break()
            document.add_heading(chapter.part, level=1)
        document.add_heading(chapter.title, level=2)
        for block in _paragraphs(chapter.body):
            document.add_paragraph(block)

    document.save(target_path)


def _compile_project_to_pdf(
    project_title: str,
    author: str,
    chapters: list[ChapterDocument],
    target_path: Path,
) -> None:
    pdf = canvas.Canvas(str(target_path), pagesize=LETTER)
    width, height = LETTER
    left_margin = 72
    right_margin = width - 72
    top_margin = height - 72
    bottom_margin = 72
    line_height = 14
    y = top_margin

    pdf.setTitle(project_title)
    if author:
        pdf.setAuthor(author)

    def new_page() -> None:
        nonlocal y
        pdf.showPage()
        pdf.setFont("Times-Roman", 12)
        y = top_margin

    def ensure_space(lines_needed: int = 1) -> None:
        nonlocal y
        if y - (lines_needed * line_height) < bottom_margin:
            new_page()

    pdf.setFont("Times-Bold", 20)
    ensure_space(2)
    pdf.drawString(left_margin, y, project_title)
    y -= line_height * 2

    if author:
        pdf.setFont("Times-Roman", 12)
        ensure_space(2)
        pdf.drawString(left_margin, y, author)
        y -= line_height * 2

    current_part = None
    for chapter in chapters:
        if chapter.part_id != current_part:
            current_part = chapter.part_id
            new_page()
            pdf.setFont("Times-Bold", 16)
            ensure_space(2)
            pdf.drawString(left_margin, y, chapter.part)
            y -= line_height * 2

        pdf.setFont("Times-Bold", 14)
        ensure_space(2)
        pdf.drawString(left_margin, y, chapter.title)
        y -= line_height * 2

        pdf.setFont("Times-Roman", 12)
        for block in _paragraphs(chapter.body):
            wrapped_lines = _wrap_pdf_text(block, right_margin - left_margin, "Times-Roman", 12)
            ensure_space(len(wrapped_lines) + 1)
            for line in wrapped_lines:
                pdf.drawString(left_margin, y, line)
                y -= line_height
            y -= line_height

    pdf.save()


def _compile_project_to_epub(
    project_title: str,
    author: str,
    chapters: list[ChapterDocument],
    target_path: Path,
) -> None:
    book = epub.EpubBook()
    book.set_identifier(f"openscribe-{target_path.stem}")
    book.set_title(project_title)
    book.set_language("en")
    if author:
        book.add_author(author)

    title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang="en")
    title_page.content = _epub_page(project_title, author, "")
    book.add_item(title_page)

    epub_items: list[epub.EpubHtml] = []
    current_part = None

    for chapter_index, chapter in enumerate(chapters, start=1):
        part_heading = ""
        if chapter.part_id != current_part:
            current_part = chapter.part_id
            part_heading = f"<h1>{escape(chapter.part)}</h1>"

        chapter_item = epub.EpubHtml(
            title=chapter.title,
            file_name=f"chapter-{chapter_index:02d}.xhtml",
            lang="en",
        )
        chapter_item.content = _epub_page(
            chapter.title,
            "",
            part_heading + _epub_body(chapter.body),
        )
        book.add_item(chapter_item)
        epub_items.append(chapter_item)

    book.toc = tuple([title_page, *epub_items])
    book.spine = ["nav", title_page, *epub_items]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    epub.write_epub(str(target_path), book, {})


def _paragraphs(text: str) -> list[str]:
    return [block.strip() for block in text.split("\n\n") if block.strip()]


def _wrap_pdf_text(text: str, max_width: float, font_name: str, font_size: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}"
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current_line = candidate
            continue
        lines.append(current_line)
        current_line = word
    lines.append(current_line)
    return lines


def _epub_page(title: str, subtitle: str, body_html: str) -> str:
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    return (
        "<html><head><title>"
        f"{escape(title)}"
        "</title></head><body>"
        f"<h1>{escape(title)}</h1>"
        f"{subtitle_html}"
        f"{body_html}"
        "</body></html>"
    )


def _epub_body(text: str) -> str:
    blocks = [f"<p>{escape(block)}</p>" for block in _paragraphs(text)]
    return "".join(blocks)
