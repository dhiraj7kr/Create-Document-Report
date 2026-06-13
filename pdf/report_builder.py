import re
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


STOPWORDS = {
    "about",
    "above",
    "after",
    "again",
    "against",
    "also",
    "among",
    "because",
    "before",
    "being",
    "between",
    "could",
    "during",
    "from",
    "have",
    "into",
    "more",
    "most",
    "other",
    "over",
    "said",
    "same",
    "some",
    "such",
    "than",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "through",
    "under",
    "were",
    "where",
    "which",
    "while",
    "with",
    "would",
}


CHAPTERS = [
    "Executive Summary",
    "Research Scope And Method",
    "Background And Context",
    "Current Developments",
    "Source-Based Analysis",
    "Conclusion",
    "References",
]


def _safe_filename(value):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    cleaned = cleaned.strip("._")
    return cleaned[:80] or "research_report"


def _clean_text(value):
    return " ".join(str(value or "").split())


def _paragraph(text, style):
    return Paragraph(escape(_clean_text(text)), style)


def _markup_paragraph(markup, style):
    return Paragraph(str(markup or ""), style)


def _split_sentences(text):
    text = _clean_text(text)
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [item.strip() for item in sentences if len(item.strip()) > 20]


def _paragraphs_from_text(text, max_chars=950):
    sentences = _split_sentences(text)
    if not sentences and text:
        return [_clean_text(text)]

    paragraphs = []
    current = []
    current_len = 0
    for sentence in sentences:
        if current and current_len + len(sentence) > max_chars:
            paragraphs.append(" ".join(current))
            current = []
            current_len = 0
        current.append(sentence)
        current_len += len(sentence)

    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def _word_counts(text):
    words = re.findall(r"[A-Za-z][A-Za-z-]{3,}", text.lower())
    return Counter(word for word in words if word not in STOPWORDS)


def _top_keywords(text, limit=8):
    return [word for word, _ in _word_counts(text).most_common(limit)]


def _extractive_summary(text, topic="", sentence_limit=5):
    sentences = _split_sentences(text)
    if len(sentences) <= sentence_limit:
        return sentences

    keyword_counts = _word_counts(text)
    topic_words = set(re.findall(r"[A-Za-z][A-Za-z-]{2,}", topic.lower()))
    scored = []
    for index, sentence in enumerate(sentences):
        words = re.findall(r"[A-Za-z][A-Za-z-]{3,}", sentence.lower())
        score = sum(keyword_counts.get(word, 0) for word in words)
        score += sum(4 for word in words if word in topic_words)
        score = score / max(len(words), 1)
        score += max(0, 1.2 - index * 0.08)
        scored.append((score, index, sentence))

    selected = sorted(scored, reverse=True)[:sentence_limit]
    return [sentence for _, _, sentence in sorted(selected, key=lambda item: item[1])]


def _article_text(item):
    return item.get("full_text") or item.get("summary") or ""


def _build_styles():
    styles = getSampleStyleSheet()

    styles["Title"].fontName = "Times-Bold"
    styles["Title"].fontSize = 30
    styles["Title"].leading = 36
    styles["Title"].alignment = TA_CENTER
    styles["Title"].textColor = colors.HexColor("#111827")

    styles["Heading1"].fontName = "Times-Bold"
    styles["Heading1"].fontSize = 18
    styles["Heading1"].leading = 23
    styles["Heading1"].spaceBefore = 18
    styles["Heading1"].spaceAfter = 8
    styles["Heading1"].textColor = colors.HexColor("#111827")

    styles["Heading2"].fontName = "Times-Bold"
    styles["Heading2"].fontSize = 13
    styles["Heading2"].leading = 17
    styles["Heading2"].spaceBefore = 10
    styles["Heading2"].spaceAfter = 5
    styles["Heading2"].textColor = colors.HexColor("#1F2937")

    styles["BodyText"].fontName = "Times-Roman"
    styles["BodyText"].fontSize = 10.5
    styles["BodyText"].leading = 15
    styles["BodyText"].alignment = TA_JUSTIFY
    styles["BodyText"].spaceAfter = 6

    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=12,
            leading=17,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#374151"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Meta",
            parent=styles["BodyText"],
            fontName="Helvetica",
            textColor=colors.HexColor("#4B5563"),
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetaCenter",
            parent=styles["Meta"],
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Lead",
            parent=styles["BodyText"],
            fontName="Times-Italic",
            fontSize=11.5,
            leading=16,
            textColor=colors.HexColor("#1F2937"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Source",
            parent=styles["BodyText"],
            fontName="Helvetica",
            textColor=colors.HexColor("#1D4ED8"),
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Toc",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ChapterNumber",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#6B7280"),
            alignment=TA_LEFT,
        )
    )
    return styles


def _rule(width=1, color="#9CA3AF", space_before=8, space_after=12):
    return HRFlowable(
        width="100%",
        thickness=width,
        color=colors.HexColor(color),
        spaceBefore=space_before,
        spaceAfter=space_after,
    )


def _chapter(story, number, title, styles):
    story.append(Spacer(1, 0.08 * inch))
    story.append(_paragraph(f"Chapter {number}", styles["ChapterNumber"]))
    story.append(_paragraph(title, styles["Heading1"]))
    story.append(_rule(width=0.7, color="#D1D5DB", space_before=2, space_after=10))


def _bullet_list(items, styles, bullet_type="bullet"):
    cleaned = [item for item in items if item]
    if not cleaned:
        return []
    return [
        ListFlowable(
            [ListItem(_paragraph(item, styles["BodyText"])) for item in cleaned],
            bulletType=bullet_type,
            leftIndent=18,
            bulletFontName="Helvetica",
        )
    ]


def _source_table(rows, styles):
    table = Table(rows, colWidths=[1.55 * inch, 4.45 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _add_cover(story, topic, wiki, news, styles):
    generated_at = datetime.now().strftime("%d %B %Y")
    source_count = (1 if wiki and wiki.get("url") else 0) + len(news)

    story.append(Spacer(1, 1.35 * inch))
    story.append(_rule(width=2.2, color="#111827", space_before=0, space_after=18))
    story.append(_paragraph(f"{topic} Research Report", styles["Title"]))
    story.append(Spacer(1, 0.18 * inch))
    story.append(
        _paragraph(
            "A structured, source-backed project report with background context, recent developments, analysis, and references.",
            styles["CoverSubtitle"],
        )
    )
    story.append(Spacer(1, 0.35 * inch))
    story.append(_rule(width=0.8, color="#9CA3AF", space_before=4, space_after=24))

    rows = [
        [_paragraph("Prepared On", styles["Meta"]), _paragraph(generated_at, styles["Meta"])],
        [_paragraph("Primary Topic", styles["Meta"]), _paragraph(topic, styles["Meta"])],
        [_paragraph("Sources Used", styles["Meta"]), _paragraph(str(source_count), styles["Meta"])],
        [_paragraph("Report Type", styles["Meta"]), _paragraph("Automated research brief for project use", styles["Meta"])],
    ]
    story.append(_source_table(rows, styles))
    story.append(Spacer(1, 1.1 * inch))
    story.append(
        _paragraph(
            "Note: This report is generated from publicly available web sources. Review references before using it for formal submission.",
            styles["MetaCenter"],
        )
    )
    story.append(PageBreak())


def _add_contents(story, styles):
    story.append(_paragraph("Contents", styles["Heading1"]))
    story.append(_rule(width=0.7, color="#D1D5DB", space_before=2, space_after=8))
    for index, chapter in enumerate(CHAPTERS, start=1):
        story.append(_markup_paragraph(f"<b>{index}.</b> {escape(chapter)}", styles["Toc"]))
    story.append(PageBreak())


def _add_executive_summary(story, topic, wiki, news, source_errors, styles):
    _chapter(story, 1, "Executive Summary", styles)

    lead_source = wiki.get("summary") if wiki else ""
    if lead_source:
        for paragraph in _paragraphs_from_text(lead_source, max_chars=850)[:3]:
            story.append(_paragraph(paragraph, styles["Lead"]))
    else:
        story.append(
            _paragraph(
                f"This report reviews available public information on {topic}. It combines reference material and recent news coverage into a structured project-ready format.",
                styles["Lead"],
            )
        )

    collected_text = " ".join(
        [wiki.get("summary", "") if wiki else ""]
        + [section.get("text", "") for section in (wiki.get("sections", []) if wiki else [])]
        + [_article_text(item) for item in news]
    )
    keywords = _top_keywords(collected_text, limit=6)
    summary_points = [
        f"The report uses {len(wiki.get('sections', [])) if wiki else 0} background section(s) and {len(news)} recent news item(s).",
        f"Important recurring terms found in the collected material include: {', '.join(keywords)}." if keywords else "",
        "Detailed article text is included where publisher pages allowed extraction.",
        f"{len(source_errors)} source issue(s) were recorded and listed in the method section." if source_errors else "",
    ]
    for flowable in _bullet_list(summary_points, styles):
        story.append(flowable)


def _add_method(story, wiki, news, source_errors, styles):
    _chapter(story, 2, "Research Scope And Method", styles)
    story.append(
        _paragraph(
            "The report is assembled from live web sources at generation time. Wikipedia is used for baseline background, while Google News RSS is used to identify recent coverage. For each news item, the generator attempts to fetch and extract readable paragraph text from the publisher page.",
            styles["BodyText"],
        )
    )

    rows = [
        [_paragraph("Source Area", styles["Meta"]), _paragraph("Collection Result", styles["Meta"])],
        [
            _paragraph("Wikipedia", styles["Meta"]),
            _paragraph(
                wiki.get("url", "No matching page returned.") if wiki else "No matching page returned.",
                styles["Source"],
            ),
        ],
        [
            _paragraph("News", styles["Meta"]),
            _paragraph(f"{len(news)} item(s) collected from Google News RSS.", styles["Meta"]),
        ],
        [
            _paragraph("Article Text", styles["Meta"]),
            _paragraph(
                f"{sum(1 for item in news if item.get('full_text'))} item(s) contained extractable publisher article text.",
                styles["Meta"],
            ),
        ],
    ]
    story.append(_source_table(rows, styles))

    if source_errors:
        story.append(_paragraph("Source Issues", styles["Heading2"]))
        for flowable in _bullet_list(source_errors, styles):
            story.append(flowable)


def _add_background(story, wiki, styles):
    _chapter(story, 3, "Background And Context", styles)
    if not wiki:
        story.append(_paragraph("No background content was available from Wikipedia for this topic.", styles["BodyText"]))
        return

    if wiki.get("url"):
        story.append(_markup_paragraph(f"<b>Reference source:</b> {escape(wiki['url'])}", styles["Source"]))
        story.append(Spacer(1, 0.08 * inch))

    for section in wiki.get("sections", []):
        story.append(_paragraph(section.get("title", "Background"), styles["Heading2"]))
        for paragraph in _paragraphs_from_text(section.get("text", ""), max_chars=950):
            story.append(_paragraph(paragraph, styles["BodyText"]))

        child_items = []
        for child in section.get("children", []):
            child_text = child.get("text")
            if child_text:
                first_sentences = " ".join(_split_sentences(child_text)[:2])
                child_items.append(f"{child.get('title')}: {first_sentences or child_text}")
        for flowable in _bullet_list(child_items[:6], styles):
            story.append(flowable)


def _add_current_developments(story, topic, news, styles):
    _chapter(story, 4, "Current Developments", styles)
    if not news:
        story.append(_paragraph("No recent news items were returned for this topic.", styles["BodyText"]))
        return

    for index, item in enumerate(news, start=1):
        title = item.get("title") or "Untitled news item"
        meta_parts = [part for part in [item.get("source"), item.get("published")] if part]
        meta = " | ".join(meta_parts) or "Source metadata unavailable"
        article_url = item.get("article_url") or item.get("link", "")
        text = _article_text(item)
        summary = _extractive_summary(text, topic=topic, sentence_limit=5)

        block = [
            _paragraph(f"{index}. {title}", styles["Heading2"]),
            _paragraph(meta, styles["Meta"]),
        ]
        if item.get("content_status"):
            block.append(_paragraph(item["content_status"], styles["Meta"]))
        block.append(_markup_paragraph(f"<b>Source:</b> {escape(article_url)}", styles["Source"]))
        story.append(KeepTogether(block))

        if summary:
            story.append(_paragraph("Detailed Summary", styles["Heading2"]))
            for paragraph in _paragraphs_from_text(" ".join(summary), max_chars=850):
                story.append(_paragraph(paragraph, styles["BodyText"]))

        if item.get("full_text"):
            key_points = _extractive_summary(item["full_text"], topic=topic, sentence_limit=4)
            story.append(_paragraph("Key Points From The Article", styles["Heading2"]))
            for flowable in _bullet_list(key_points, styles):
                story.append(flowable)
        elif item.get("summary"):
            story.append(_paragraph("Available RSS Detail", styles["Heading2"]))
            story.append(_paragraph(item["summary"], styles["BodyText"]))

        story.append(Spacer(1, 0.1 * inch))


def _add_analysis(story, topic, wiki, news, styles):
    _chapter(story, 5, "Source-Based Analysis", styles)

    background_text = " ".join(
        [wiki.get("summary", "") if wiki else ""]
        + [section.get("text", "") for section in (wiki.get("sections", []) if wiki else [])]
    )
    news_text = " ".join(_article_text(item) for item in news)
    all_text = f"{background_text} {news_text}"

    story.append(_paragraph("Main Themes", styles["Heading2"]))
    keywords = _top_keywords(all_text, limit=10)
    if keywords:
        for flowable in _bullet_list([keyword.title() for keyword in keywords], styles):
            story.append(flowable)
    else:
        story.append(_paragraph("No recurring themes could be extracted from the available text.", styles["BodyText"]))

    story.append(_paragraph("Observations", styles["Heading2"]))
    observations = []
    if wiki:
        observations.append(
            f"The background source provides a reference foundation for {topic}, including {len(wiki.get('sections', []))} structured section(s)."
        )
    if news:
        extracted = sum(1 for item in news if item.get("full_text"))
        observations.append(
            f"Recent coverage adds current context through {len(news)} news item(s), with detailed article text extracted for {extracted} item(s)."
        )
    if keywords:
        observations.append(
            f"The collected material repeatedly emphasizes {', '.join(keywords[:5])}, making these useful areas for project discussion."
        )
    observations.append(
        "Use the references section to verify every important claim before final academic, business, or client submission."
    )
    for flowable in _bullet_list(observations, styles):
        story.append(flowable)

    story.append(_paragraph("Limitations", styles["Heading2"]))
    limitations = [
        "Some publisher sites block automated article extraction, so the report may use RSS summaries for those items.",
        "The report is extractive and source-backed; it does not replace expert review or original research.",
        "News coverage changes over time, so regenerate the report when current information is important.",
    ]
    for flowable in _bullet_list(limitations, styles):
        story.append(flowable)


def _add_conclusion(story, topic, wiki, news, styles):
    _chapter(story, 6, "Conclusion", styles)

    conclusion_parts = []
    if wiki and wiki.get("summary"):
        conclusion_parts.extend(_extractive_summary(wiki["summary"], topic=topic, sentence_limit=2))
    if news:
        latest_titles = [item.get("title") for item in news[:3] if item.get("title")]
        if latest_titles:
            conclusion_parts.append(
                f"Recent coverage reviewed for this report includes: {'; '.join(latest_titles)}."
            )

    if not conclusion_parts:
        conclusion_parts.append(
            f"The available material for {topic} was limited, but the report captures the source status and references for follow-up research."
        )

    for paragraph in conclusion_parts:
        story.append(_paragraph(paragraph, styles["BodyText"]))

    story.append(
        _paragraph(
            "For project use, the strongest next step is to convert the themes, background facts, and current developments into your own argument, supported by the references listed below.",
            styles["Lead"],
        )
    )


def _add_references(story, wiki, news, styles):
    _chapter(story, 7, "References", styles)

    items = []
    if wiki and wiki.get("url"):
        items.append(f"Wikipedia - {wiki.get('title', 'Topic page')}: {wiki['url']}")
    for item in news:
        title = item.get("title", "News item")
        source = item.get("source", "Publisher")
        published = item.get("published", "date unavailable")
        url = item.get("article_url") or item.get("link", "")
        items.append(f"{source} ({published}) - {title}: {url}")

    if not items:
        story.append(_paragraph("No external sources were available.", styles["BodyText"]))
        return

    story.append(
        ListFlowable(
            [ListItem(_paragraph(item, styles["Source"])) for item in items],
            bulletType="1",
            leftIndent=18,
            bulletFontName="Helvetica",
        )
    )


def _page_frame(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
    canvas.setLineWidth(0.35)
    canvas.line(0.62 * inch, height - 0.48 * inch, width - 0.62 * inch, height - 0.48 * inch)
    canvas.line(0.62 * inch, 0.48 * inch, width - 0.62 * inch, 0.48 * inch)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(0.65 * inch, height - 0.38 * inch, "Research Report")
    canvas.drawRightString(width - 0.65 * inch, 0.31 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_report(topic, wiki, news, output_dir="reports", source_errors=None):
    source_errors = source_errors or []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    filename = f"{_safe_filename(topic)}_Report.pdf"
    report_path = output_path / filename

    doc = SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.76 * inch,
        bottomMargin=0.72 * inch,
        title=f"{topic} Research Report",
        author="Research Report Generator",
    )
    styles = _build_styles()
    story = []

    _add_cover(story, topic, wiki, news, styles)
    _add_contents(story, styles)
    _add_executive_summary(story, topic, wiki, news, source_errors, styles)
    _add_method(story, wiki, news, source_errors, styles)
    _add_background(story, wiki, styles)
    _add_current_developments(story, topic, news, styles)
    _add_analysis(story, topic, wiki, news, styles)
    _add_conclusion(story, topic, wiki, news, styles)
    _add_references(story, wiki, news, styles)

    doc.build(story, onFirstPage=_page_frame, onLaterPages=_page_frame)
    return report_path.resolve()
