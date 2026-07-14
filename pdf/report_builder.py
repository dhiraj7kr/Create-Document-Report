import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from html import escape

from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    BalancedColumns,
    KeepTogether
)

# Professional Editorial Color Palette
PRIMARY_COLOR = HexColor("#1A365D")    # Deep Navy
SECONDARY_COLOR = HexColor("#2B6CB0")  # Slate Blue
TEXT_COLOR = HexColor("#2D3748")       # Dark Charcoal
MUTED_TEXT = HexColor("#718096")       # Cool Grey
ACCENT_LINE = HexColor("#E2E8F0")      # Light Border Grey
BG_LIGHT = HexColor("#F8F9FA")         # Soft Off-White for Tables/Callouts


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render running headers
    and 'Page X of Y' footers, cleanly suppressing them on the cover page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress running headers and footers on cover page

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(MUTED_TEXT)

        width, height = self._pagesize
        margin = 0.75 * inch

        # Running Header
        self.drawString(margin, height - 36, "Executive Research Dossier & Intelligence Synthesis")
        self.setStrokeColor(ACCENT_LINE)
        self.setLineWidth(0.75)
        self.line(margin, height - 42, width - margin, height - 42)

        # Running Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(width - margin, 36, page_str)
        self.line(margin, 48, width - margin, 48)

        self.restoreState()


def safe_filename(text):
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", str(text))
    return text[:100]


def clean_text(value):
    return " ".join(str(value or "").split())


def paragraph(text, style):
    return Paragraph(escape(clean_text(text)), style)


def build_styles():
    styles = getSampleStyleSheet()

    styles["Title"].fontName = "Helvetica-Bold"
    styles["Title"].fontSize = 26
    styles["Title"].leading = 32
    styles["Title"].textColor = PRIMARY_COLOR
    styles["Title"].alignment = TA_LEFT
    styles["Title"].spaceAfter = 12

    styles["Heading1"].fontName = "Helvetica-Bold"
    styles["Heading1"].fontSize = 16
    styles["Heading1"].leading = 20
    styles["Heading1"].textColor = PRIMARY_COLOR
    styles["Heading1"].spaceBefore = 18
    styles["Heading1"].spaceAfter = 8
    styles["Heading1"].keepWithNext = True

    styles["Heading2"].fontName = "Helvetica-Bold"
    styles["Heading2"].fontSize = 12
    styles["Heading2"].leading = 16
    styles["Heading2"].textColor = SECONDARY_COLOR
    styles["Heading2"].spaceBefore = 12
    styles["Heading2"].spaceAfter = 6
    styles["Heading2"].keepWithNext = True

    styles["BodyText"].fontName = "Helvetica"
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 15
    styles["BodyText"].textColor = TEXT_COLOR
    styles["BodyText"].alignment = TA_JUSTIFY
    styles["BodyText"].spaceAfter = 8
    styles["BodyText"].firstLineIndent = 12

    styles.add(
        ParagraphStyle(
            name="BodyNoIndent",
            parent=styles["BodyText"],
            firstLineIndent=0,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Meta",
            parent=styles["BodyNoIndent"],
            fontSize=8.5,
            leading=12,
            textColor=MUTED_TEXT,
            alignment=TA_LEFT,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["BodyNoIndent"],
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            textColor=SECONDARY_COLOR,
            spaceAfter=24,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ImageCaption",
            parent=styles["BodyNoIndent"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=MUTED_TEXT,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=10,
        )
    )

    return styles


def add_rule(story, space_before=4, space_after=12, color=ACCENT_LINE, thickness=1):
    if space_before > 0:
        story.append(Spacer(1, space_before))
    story.append(HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=space_after))


def add_cover_page(story, topic, knowledge, styles):
    story.append(Spacer(1, 1.5 * inch))

    # Thick decorative primary accent bar
    add_rule(story, space_before=0, space_after=16, color=PRIMARY_COLOR, thickness=4)

    story.append(paragraph(topic, styles["Title"]))
    story.append(paragraph("Executive Intelligence Dossier & Comprehensive Research Synthesis", styles["CoverSubtitle"]))

    story.append(Spacer(1, 3.5 * inch))

    stats = knowledge.get("statistics", {})
    meta_text = (
        f"<b>Generated:</b> {datetime.now().strftime('%d %B %Y | %H:%M')}<br/>"
        f"<b>Data Sources Analyzed:</b> {stats.get('news', 0)} News Streams, "
        f"{stats.get('articles', 0)} Deep Web Crawls, {stats.get('images', 0)} Visual Assets<br/>"
        f"<b>Classification:</b> Automated AI Intelligence Synthesis"
    )
    story.append(Paragraph(meta_text, styles["Meta"]))
    add_rule(story, space_before=6, space_after=0, color=ACCENT_LINE, thickness=0.5)

    story.append(PageBreak())


def add_contents(story, styles, chapters):
    story.append(paragraph("Table of Contents", styles["Heading1"]))
    add_rule(story, color=PRIMARY_COLOR, thickness=1.5)

    for index, chapter in enumerate(chapters, start=1):
        chapter_text = f"<b>{index}.0</b> &nbsp;&nbsp; {chapter}"
        story.append(Paragraph(chapter_text, styles["BodyNoIndent"]))
        add_rule(story, space_before=4, space_after=8, color=ACCENT_LINE, thickness=0.5)

    story.append(PageBreak())


def add_section_header(story, title, styles):
    story.append(paragraph(title, styles["Heading1"]))
    add_rule(story, color=PRIMARY_COLOR, thickness=1.5, space_after=14)

def format_image_flowable(image_path, caption_text, width, height, styles):
    """Wraps an image in a professional border with a muted caption."""
    try:
        if not os.path.exists(image_path):
            return None
        with PILImage.open(image_path) as img:
            img.verify()
        
        img_flowable = Image(image_path, width=width, height=height)
        
        # Structure image and caption into a bordered Table frame
        frame_table = Table(
            [[img_flowable], [Paragraph(escape(clean_text(caption_text)), styles["ImageCaption"])]],
            colWidths=[width + 8]
        )
        frame_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, ACCENT_LINE),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, 1), 2),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
        ]))
        
        # Return the table directly WITHOUT wrapping it in KeepTogether
        return frame_table
    except Exception:
        return None

def add_introduction(story, knowledge, styles):
    add_section_header(story, "1.0 Executive Summary & Introduction", styles)

    wiki = knowledge.get("wiki", {})
    summary = wiki.get("summary", "")

    if summary:
        # Wrap introduction into a balanced 2-column layout
        intro_flowables = [paragraph(p, styles["BodyText"]) for p in summary.split("\n\n") if p.strip()]
        story.append(BalancedColumns(intro_flowables, nCols=2))
    else:
        story.append(paragraph("No introductory summary available in the primary data repository.", styles["Meta"]))

    story.append(PageBreak())


def add_image_gallery(story, knowledge, styles):
    images = knowledge.get("images", [])
    if not images:
        return

    add_section_header(story, "2.0 Visual Intelligence Gallery", styles)

    valid_frames = []
    for idx, image_path in enumerate(images, start=1):
        frame = format_image_flowable(
            image_path, 
            f"Figure 2.{idx} — Visual asset retrieved via targeted crawl.", 
            width=2.9 * inch, 
            height=1.9 * inch, 
            styles=styles
        )
        if frame:
            valid_frames.append(frame)
            if len(valid_frames) >= 6:  # Max 6 images for a 2x3 grid
                break

    if not valid_frames:
        story.append(paragraph("No high-resolution visual assets could be verified for presentation.", styles["Meta"]))
        story.append(PageBreak())
        return

    # Organize frames into a 2-column Table grid
    table_data = []
    for i in range(0, len(valid_frames), 2):
        row = valid_frames[i:i + 2]
        if len(row) == 1:
            row.append("")
        table_data.append(row)

    grid_table = Table(table_data, colWidths=[3.25 * inch, 3.25 * inch])
    grid_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    story.append(grid_table)
    story.append(PageBreak())


def add_background_section(story, knowledge, styles):
    add_section_header(story, "3.0 Deep Dive: Career, History & Contributions", styles)

    wiki = knowledge.get("wiki", {})
    sections = wiki.get("sections", [])

    if not sections:
        story.append(paragraph("No structured historical background available in the repository.", styles["Meta"]))
        story.append(PageBreak())
        return

    section_flowables = []
    for section in sections:
        title = section.get("title", "")
        text = section.get("text", "")

        if title:
            section_flowables.append(paragraph(title, styles["Heading2"]))
        if text:
            for p in text.split("\n\n"):
                if p.strip():
                    section_flowables.append(paragraph(p, styles["BodyText"]))

        for child in section.get("children", []):
            child_title = child.get("title", "")
            child_text = child.get("text", "")

            if child_title:
                section_flowables.append(paragraph(child_title, styles["Heading2"]))
            if child_text:
                for p in child_text.split("\n\n"):
                    if p.strip():
                        section_flowables.append(paragraph(p, styles["BodyText"]))

        section_flowables.append(Spacer(1, 8))

    # Render body background in a 2-column magazine layout
    story.append(BalancedColumns(section_flowables, nCols=2))
    story.append(PageBreak())


def add_recent_developments(story, knowledge, styles):
    add_section_header(story, "4.0 Current Developments & Live News Intelligence", styles)

    news = knowledge.get("news", [])
    if not news:
        story.append(paragraph("No recent news developments harvested for this briefing.", styles["BodyNoIndent"]))
        story.append(PageBreak())
        return

    news_flowables = []
    for article in news:
        title = article.get("title", "Untitled Article")
        news_flowables.append(paragraph(title, styles["Heading2"]))

        meta_parts = [part for part in [article.get("source"), article.get("published")] if part]
        if meta_parts:
            news_flowables.append(paragraph(" &bull; ".join(meta_parts), styles["Meta"]))

        article_text = article.get("full_text") or article.get("summary") or ""
        if article_text:
            for p in article_text.split("\n\n"):
                if p.strip():
                    news_flowables.append(paragraph(p, styles["BodyText"]))

        news_flowables.append(Spacer(1, 4))
        news_flowables.append(HRFlowable(width="100%", thickness=0.5, color=ACCENT_LINE, spaceAfter=10))

    story.append(BalancedColumns(news_flowables, nCols=2))
    story.append(PageBreak())


def add_references(story, knowledge, styles):
    add_section_header(story, "5.0 Source Repository & References", styles)

    references = []
    wiki = knowledge.get("wiki", {})
    if wiki.get("url"):
        references.append(wiki["url"])

    for article in knowledge.get("news", []):
        url = article.get("article_url") or article.get("url") or article.get("link")
        if url:
            references.append(url)

    for article in knowledge.get("articles", []):
        url = article.get("url")
        if url:
            references.append(url)

    references = list(dict.fromkeys(references))

    if not references:
        story.append(paragraph("No references available.", styles["BodyNoIndent"]))
        return

    bullets = []
    for ref in references:
        ref_link = f'<font color="#2B6CB0"><u>{escape(ref)}</u></font>'
        bullets.append(ListItem(Paragraph(ref_link, styles["BodyNoIndent"]), leftIndent=20))

    story.append(ListFlowable(bullets, bulletType="1", start=1, bulletFontName="Helvetica-Bold"))


def build_report(topic, knowledge, output_dir="reports", research_plan=None):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = safe_filename(topic) + "_Executive_Report.pdf"
    llm_payload_path = output_path / f"{safe_filename(topic)}_knowledge.json"

    with open(llm_payload_path, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, indent=4)
    logging.info("Saved raw knowledge dataset for AI optimization to %s", llm_payload_path)

    report_path = output_path / filename

    doc = SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = build_styles()
    story = []

    # Derive table of contents from AI planner or use default structure
    default_chapters = [
        "Executive Summary & Introduction",
        "Visual Intelligence Gallery",
        "Deep Dive: Career, History & Contributions",
        "Current Developments & Live News Intelligence",
        "Source Repository & References"
    ]
    chapters = research_plan.get("chapters", default_chapters) if research_plan else default_chapters

    add_cover_page(story, topic, knowledge, styles)
    add_contents(story, styles, chapters)
    add_introduction(story, knowledge, styles)
    add_image_gallery(story, knowledge, styles)
    add_background_section(story, knowledge, styles)
    add_recent_developments(story, knowledge, styles)
    add_references(story, knowledge, styles)

    # Build PDF using the dynamic two-pass NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)

    return report_path.resolve()