import os
import re
from datetime import datetime
from pathlib import Path
from html import escape

from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
    TA_JUSTIFY,
    TA_LEFT
)

from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet
)

from reportlab.lib.units import inch

from reportlab.platypus import (
    Paragraph,
    Spacer,
    PageBreak,
    SimpleDocTemplate,
    Image,
    HRFlowable,
    ListFlowable,
    ListItem
)


CHAPTERS = [
    "Introduction",
    "Image Gallery",
    "Career and Contributions",
    "Recent Developments",
    "References"
]


def safe_filename(text):

    text = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        text
    )

    return text[:100]


def clean_text(value):

    return " ".join(
        str(value or "").split()
    )


def paragraph(
    text,
    style
):

    return Paragraph(
        escape(
            clean_text(text)
        ),
        style
    )


def build_styles():

    styles = getSampleStyleSheet()

    styles["Title"].fontName = "Times-Bold"
    styles["Title"].fontSize = 32
    styles["Title"].leading = 40
    styles["Title"].alignment = TA_CENTER

    styles["Heading1"].fontSize = 22
    styles["Heading1"].leading = 28

    styles["Heading2"].fontSize = 16
    styles["Heading2"].leading = 22

    styles["BodyText"].fontSize = 11
    styles["BodyText"].leading = 18
    styles["BodyText"].alignment = TA_JUSTIFY

    styles.add(
        ParagraphStyle(
            name="Meta",
            parent=styles["BodyText"],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_LEFT
        )
    )

    return styles


def add_rule(story):

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.7,
            color=colors.lightgrey
        )
    )

    story.append(
        Spacer(
            1,
            8
        )
    )


def add_cover_page(
    story,
    topic,
    knowledge,
    styles
):

    story.append(
        Spacer(
            1,
            2 * inch
        )
    )

    story.append(
        paragraph(
            topic,
            styles["Title"]
        )
    )

    story.append(
        Spacer(
            1,
            25
        )
    )

    story.append(
        paragraph(
            "A Comprehensive Research Biography",
            styles["Heading2"]
        )
    )

    story.append(
        Spacer(
            1,
            50
        )
    )

    story.append(
        paragraph(
            datetime.now().strftime(
                "%d %B %Y"
            ),
            styles["Meta"]
        )
    )

    story.append(
        PageBreak()
    )


def add_contents(
    story,
    styles
):

    story.append(
        paragraph(
            "Contents",
            styles["Heading1"]
        )
    )

    add_rule(story)

    for index, chapter in enumerate(
        CHAPTERS,
        start=1
    ):

        story.append(
            paragraph(
                f"{index}. {chapter}",
                styles["BodyText"]
            )
        )

    story.append(
        PageBreak()
    )


def add_introduction(
    story,
    knowledge,
    styles
):

    story.append(
        paragraph(
            "Chapter 1",
            styles["Heading1"]
        )
    )

    story.append(
        paragraph(
            "Introduction",
            styles["Heading2"]
        )
    )

    add_rule(story)

    wiki = knowledge.get(
        "wiki",
        {}
    )

    summary = wiki.get(
        "summary",
        ""
    )

    if summary:

        story.append(
            paragraph(
                summary,
                styles["BodyText"]
            )
        )

    story.append(
        PageBreak()
    )


def add_image_gallery(
    story,
    knowledge,
    styles
):

    images = knowledge.get(
        "images",
        []
    )

    if not images:
        return

    story.append(
        paragraph(
            "Chapter 2",
            styles["Heading1"]
        )
    )

    story.append(
        paragraph(
            "Image Gallery",
            styles["Heading2"]
        )
    )

    add_rule(story)

    count = 0

    for image_path in images:

        try:

            if not os.path.exists(
                image_path
            ):
                continue

            try:

                with PILImage.open(
                    image_path
                ) as img:

                    img.verify()

            except Exception:
                continue

            image = Image(
                image_path,
                width=4 * inch,
                height=2.8 * inch
            )

            story.append(
                image
            )

            story.append(
                Spacer(
                    1,
                    12
                )
            )

            count += 1

            if count >= 8:
                break

        except Exception:
            continue

    story.append(
        PageBreak()
    )


def add_background_section(
    story,
    knowledge,
    styles
):

    story.append(
        paragraph(
            "Chapter 3",
            styles["Heading1"]
        )
    )

    story.append(
        paragraph(
            "Career and Contributions",
            styles["Heading2"]
        )
    )

    add_rule(story)

    wiki = knowledge.get(
        "wiki",
        {}
    )

    sections = wiki.get(
        "sections",
        []
    )

    for section in sections:

        title = section.get(
            "title",
            ""
        )

        text = section.get(
            "text",
            ""
        )

        if title:

            story.append(
                paragraph(
                    title,
                    styles["Heading2"]
                )
            )

        if text:

            story.append(
                paragraph(
                    text,
                    styles["BodyText"]
                )
            )

        children = section.get(
            "children",
            []
        )

        for child in children:

            child_title = child.get(
                "title",
                ""
            )

            child_text = child.get(
                "text",
                ""
            )

            if child_title:

                story.append(
                    paragraph(
                        child_title,
                        styles["Heading2"]
                    )
                )

            if child_text:

                story.append(
                    paragraph(
                        child_text,
                        styles["BodyText"]
                    )
                )

            story.append(
                Spacer(
                    1,
                    6
                )
            )

    story.append(
        PageBreak()
    )

def add_recent_developments(
    story,
    knowledge,
    styles
):

    story.append(
        paragraph(
            "Chapter 4",
            styles["Heading1"]
        )
    )

    story.append(
        paragraph(
            "Recent Developments and Current Work",
            styles["Heading2"]
        )
    )

    add_rule(story)

    news = knowledge.get(
        "news",
        []
    )

    if not news:

        story.append(
            paragraph(
                "No recent developments available.",
                styles["BodyText"]
            )
        )

        story.append(
            PageBreak()
        )

        return

    for article in news:

        title = article.get(
            "title",
            "Untitled"
        )

        story.append(
            paragraph(
                title,
                styles["Heading2"]
            )
        )

        meta_parts = []

        if article.get("source"):
            meta_parts.append(
                article["source"]
            )

        if article.get("published"):
            meta_parts.append(
                article["published"]
            )

        if meta_parts:

            story.append(
                paragraph(
                    " | ".join(meta_parts),
                    styles["Meta"]
                )
            )

        article_text = (
            article.get("full_text")
            or article.get("summary")
            or ""
        )

        if article_text:

            story.append(
                paragraph(
                    article_text,
                    styles["BodyText"]
                )
            )

        story.append(
            Spacer(
                1,
                12
            )
        )

    story.append(
        PageBreak()
    )


def add_references(
    story,
    knowledge,
    styles
):

    story.append(
        paragraph(
            "References",
            styles["Heading1"]
        )
    )

    add_rule(story)

    references = []

    wiki = knowledge.get(
        "wiki",
        {}
    )

    if wiki.get("url"):

        references.append(
            wiki["url"]
        )

    for article in knowledge.get(
        "news",
        []
    ):

        url = (
            article.get("article_url")
            or article.get("url")
        )

        if url:
            references.append(url)

    for article in knowledge.get(
        "articles",
        []
    ):

        url = article.get(
            "url"
        )

        if url:
            references.append(url)

    references = list(
        dict.fromkeys(
            references
        )
    )

    if not references:

        story.append(
            paragraph(
                "No references available.",
                styles["BodyText"]
            )
        )

        return

    bullets = []

    for ref in references:

        bullets.append(
            ListItem(
                paragraph(
                    ref,
                    styles["BodyText"]
                )
            )
        )

    story.append(
        ListFlowable(
            bullets,
            bulletType="1"
        )
    )


def build_report(
    topic,
    knowledge,
    output_dir="reports"
):

    output_path = Path(
        output_dir
    )

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        safe_filename(topic)
        + "_Report.pdf"
    )

    report_path = (
        output_path
        / filename
    )

    doc = SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    styles = build_styles()

    story = []

    add_cover_page(
        story,
        topic,
        knowledge,
        styles
    )

    add_contents(
        story,
        styles
    )

    add_introduction(
        story,
        knowledge,
        styles
    )

    add_image_gallery(
        story,
        knowledge,
        styles
    )

    add_background_section(
        story,
        knowledge,
        styles
    )

    add_recent_developments(
        story,
        knowledge,
        styles
    )

    add_references(
        story,
        knowledge,
        styles
    )

    doc.build(
        story
    )

    return report_path.resolve()