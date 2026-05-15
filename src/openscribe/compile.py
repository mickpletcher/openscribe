from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(slots=True)
class CompileOptions:
    format_name: str
    template_name: str
    output_filename: str
    include_title_page: bool
    include_part_headings: bool
    chapter_heading_style: str


TEMPLATE_PRESETS = {
    "novel": {
        "include_title_page": True,
        "include_part_headings": True,
        "chapter_heading_style": "title-only",
    },
    "manuscript": {
        "include_title_page": True,
        "include_part_headings": False,
        "chapter_heading_style": "chapter-number-title",
    },
    "minimal": {
        "include_title_page": False,
        "include_part_headings": False,
        "chapter_heading_style": "title-only",
    },
}


def compile_project(
    root: Path,
    format_name: str | None = None,
    template_name: str | None = None,
    output_path: Path | None = None,
) -> Path:
    config = load_project_config(root)
    project_title = str(config.get("title", "Untitled Project"))
    options = _resolve_compile_options(config, format_name, template_name, output_path)
    chapters = _compiled_chapters(root)
    target_path = output_path or default_output_path(root, project_title, options)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if options.format_name == "docx":
        _compile_project_to_docx(
            project_title,
            str(config.get("author", "")).strip(),
            chapters,
            target_path,
            options,
        )
        return target_path
    if options.format_name == "pdf":
        _compile_project_to_pdf(
            project_title,
            str(config.get("author", "")).strip(),
            chapters,
            target_path,
            options,
        )
        return target_path
    if options.format_name == "epub":
        _compile_project_to_epub(
            project_title,
            str(config.get("author", "")).strip(),
            chapters,
            target_path,
            options,
        )
        return target_path

    raise CompileError(
        f"Format '{options.format_name}' is not supported yet. Use docx, pdf, or epub."
    )


def assemble_manuscript_text(root: Path, template_name: str | None = None) -> str:
    config = load_project_config(root)
    project_title = str(config.get("title", "Untitled Project"))
    author = str(config.get("author", "")).strip()
    options = _resolve_compile_options(config, None, template_name, None)
    chapters = _compiled_chapters(root)

    sections: list[str] = []
    if options.include_title_page:
        title_lines = [project_title]
        if author:
            title_lines.append(author)
        sections.append("\n".join(title_lines))

    current_part = None
    for chapter_number, chapter in enumerate(chapters, start=1):
        if chapter.part_id != current_part:
            current_part = chapter.part_id
            if options.include_part_headings:
                sections.append(chapter.part)

        chapter_heading = _chapter_heading(chapter.title, chapter_number, options)
        chapter_sections = [chapter_heading, chapter.body.strip()]
        sections.append("\n\n".join([part for part in chapter_sections if part]))

    return "\n\n".join(section for section in sections if section.strip())


def default_output_path(root: Path, project_title: str, options: CompileOptions) -> Path:
    if options.output_filename.strip():
        filename = options.output_filename.strip()
    else:
        filename = slugify(project_title)

    if not filename.lower().endswith(f".{options.format_name}"):
        filename = f"{filename}.{options.format_name}"
    return root / "build" / filename


def _resolve_format(config: dict, format_name: str | None, output_path: Path | None) -> str:
    if format_name:
        return format_name.strip().lower()
    if output_path and output_path.suffix:
        return output_path.suffix.lstrip(".").lower()
    compile_config = config.get("compile", {})
    return str(compile_config.get("default_format", "docx")).lower()


def _resolve_compile_options(
    config: dict,
    format_name: str | None,
    template_name: str | None,
    output_path: Path | None,
) -> CompileOptions:
    compile_config = config.get("compile", {})
    explicit_template = template_name is not None
    resolved_template = (template_name or str(compile_config.get("default_template", "novel"))).strip().lower()
    if resolved_template not in TEMPLATE_PRESETS:
        supported = ", ".join(sorted(TEMPLATE_PRESETS))
        raise CompileError(
            f"Template '{resolved_template}' is not supported yet. Use {supported}."
        )

    template_defaults = TEMPLATE_PRESETS[resolved_template]
    chapter_heading_style_source = (
        template_defaults["chapter_heading_style"]
        if explicit_template
        else compile_config.get("chapter_heading_style", template_defaults["chapter_heading_style"])
    )
    chapter_heading_style = str(chapter_heading_style_source).strip().lower()
    if chapter_heading_style not in {"title-only", "chapter-number-title"}:
        raise CompileError(
            "chapter_heading_style must be 'title-only' or 'chapter-number-title'."
        )

    return CompileOptions(
        format_name=_resolve_format(config, format_name, output_path),
        template_name=resolved_template,
        output_filename=str(compile_config.get("output_filename", "") or "").strip(),
        include_title_page=bool(
            template_defaults["include_title_page"]
            if explicit_template
            else compile_config.get("include_title_page", template_defaults["include_title_page"])
        ),
        include_part_headings=bool(
            template_defaults["include_part_headings"]
            if explicit_template
            else compile_config.get("include_part_headings", template_defaults["include_part_headings"])
        ),
        chapter_heading_style=chapter_heading_style,
    )


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
    options: CompileOptions,
) -> None:
    document = Document()
    document.core_properties.title = project_title
    if author:
        document.core_properties.author = author

    if options.include_title_page:
        document.add_heading(project_title, level=0)
        if author:
            document.add_paragraph(author)

    current_part = None
    for chapter_number, chapter in enumerate(chapters, start=1):
        if chapter.part_id != current_part:
            current_part = chapter.part_id
            if options.include_part_headings:
                document.add_page_break()
                document.add_heading(chapter.part, level=1)
        document.add_heading(_chapter_heading(chapter.title, chapter_number, options), level=2)
        for block in _paragraphs(chapter.body):
            document.add_paragraph(block)

    document.save(target_path)


def _compile_project_to_pdf(
    project_title: str,
    author: str,
    chapters: list[ChapterDocument],
    target_path: Path,
    options: CompileOptions,
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

    if options.include_title_page:
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
    for chapter_number, chapter in enumerate(chapters, start=1):
        if chapter.part_id != current_part:
            current_part = chapter.part_id
            if options.include_part_headings:
                new_page()
                pdf.setFont("Times-Bold", 16)
                ensure_space(2)
                pdf.drawString(left_margin, y, chapter.part)
                y -= line_height * 2

        pdf.setFont("Times-Bold", 14)
        ensure_space(2)
        pdf.drawString(left_margin, y, _chapter_heading(chapter.title, chapter_number, options))
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
    options: CompileOptions,
) -> None:
    book = epub.EpubBook()
    book.set_identifier(f"openscribe-{target_path.stem}")
    book.set_title(project_title)
    book.set_language("en")
    if author:
        book.add_author(author)

    title_page = None
    if options.include_title_page:
        title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang="en")
        title_page.content = _epub_page(project_title, author, "")
        book.add_item(title_page)

    epub_items: list[epub.EpubHtml] = []
    current_part = None

    for chapter_index, chapter in enumerate(chapters, start=1):
        part_heading = ""
        if chapter.part_id != current_part:
            current_part = chapter.part_id
            if options.include_part_headings:
                part_heading = f"<h1>{escape(chapter.part)}</h1>"

        chapter_item = epub.EpubHtml(
            title=_chapter_heading(chapter.title, chapter_index, options),
            file_name=f"chapter-{chapter_index:02d}.xhtml",
            lang="en",
        )
        chapter_item.content = _epub_page(
            _chapter_heading(chapter.title, chapter_index, options),
            "",
            part_heading + _epub_body(chapter.body),
        )
        book.add_item(chapter_item)
        epub_items.append(chapter_item)

    if title_page is not None:
        book.toc = tuple([title_page, *epub_items])
        book.spine = ["nav", title_page, *epub_items]
    else:
        book.toc = tuple(epub_items)
        book.spine = ["nav", *epub_items]
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


def _chapter_heading(title: str, chapter_number: int, options: CompileOptions) -> str:
    if options.chapter_heading_style == "chapter-number-title":
        return f"Chapter {chapter_number}: {title}"
    return title
