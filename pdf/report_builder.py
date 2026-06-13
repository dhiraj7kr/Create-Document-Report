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
    ListItem,
    Table,
    TableStyle
)


CHAPTERS = [
    "Executive Summary",
    "Background Information",
    "Timeline",
    "Key Facts",
    "Recent Developments",
    "Analysis",
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
        escape(clean_text(text)),
        style
    )


def build_styles():

    styles = getSampleStyleSheet()

    styles["Title"].fontName = "Times-Bold"
    styles["Title"].fontSize = 28
    styles["Title"].leading = 34
    styles["Title"].alignment = TA_CENTER

    styles["Heading1"].fontSize = 18
    styles["Heading1"].leading = 24

    styles["Heading2"].fontSize = 13
    styles["Heading2"].leading = 18

    styles["BodyText"].fontSize = 10.5
    styles["BodyText"].leading = 15
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
            1.2 * inch
        )
    )

    story.append(
        paragraph(
            f"{topic} Research Report",
            styles["Title"]
        )
    )

    story.append(
        Spacer(
            1,
            20
        )
    )

    add_rule(story)

    story.append(
        paragraph(
            (
                "Detailed Research Report "
                "Generated From Multiple Sources"
            ),
            styles["Heading2"]
        )
    )

    story.append(
        Spacer(
            1,
            20
        )
    )

    rows = [
        [
            "Topic",
            topic
        ],
        [
            "Generated On",
            datetime.now().strftime(
                "%d %B %Y"
            )
        ],
        [
            "Articles",
            str(
                len(
                    knowledge.get(
                        "articles",
                        []
                    )
                )
            )
        ],
        [
            "News Items",
            str(
                len(
                    knowledge.get(
                        "news",
                        []
                    )
                )
            )
        ],
        [
            "Images",
            str(
                len(
                    knowledge.get(
                        "images",
                        []
                    )
                )
            )
        ]
    ]

    table = Table(
        rows,
        colWidths=[
            2 * inch,
            4 * inch
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.black
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                )
            ]
        )
    )

    story.append(table)

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


def add_executive_summary(
    story,
    knowledge,
    styles
):

    story.append(
        paragraph(
            "Executive Summary",
            styles["Heading1"]
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

    keywords = knowledge.get(
        "keywords",
        []
    )

    if keywords:

        story.append(
            Spacer(
                1,
                10
            )
        )

        story.append(
            paragraph(
                "Key Topics",
                styles["Heading2"]
            )
        )

        bullet_items = []

        for keyword in keywords[:15]:

            bullet_items.append(
                ListItem(
                    paragraph(
                        keyword.title(),
                        styles["BodyText"]
                    )
                )
            )

        story.append(
            ListFlowable(
                bullet_items,
                bulletType="bullet"
            )
        )

    story.append(
        PageBreak()
    )


def add_timeline(
    story,
    knowledge,
    styles
):

    story.append(
        paragraph(
            "Timeline",
            styles["Heading1"]
        )
    )

    add_rule(story)

    timeline = knowledge.get(
        "timeline",
        []
    )

    if not timeline:

        story.append(
            paragraph(
                "No timeline data found.",
                styles["BodyText"]
            )
        )

        return

    rows = [
        [
            "Year",
            "Mentions"
        ]
    ]

    for item in timeline:

        rows.append(
            [
                item["year"],
                str(
                    item["mentions"]
                )
            ]
        )

    table = Table(
        rows,
        colWidths=[
            2 * inch,
            2 * inch
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.black
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                )
            ]
        )
    )

    story.append(table)

    story.append(
        PageBreak()
    )


def add_key_facts(
    story,
    knowledge,
    styles
):

    story.append(
        paragraph(
            "Key Facts",
            styles["Heading1"]
        )
    )

    add_rule(story)

    facts = knowledge.get(
        "facts",
        []
    )

    bullets = []

    for fact in facts[:40]:

        bullets.append(
            ListItem(
                paragraph(
                    fact,
                    styles["BodyText"]
                )
            )
        )

    story.append(
        ListFlowable(
            bullets,
            bulletType="bullet"
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
            "Image Gallery",
            styles["Heading1"]
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
                 with PILImage.open(image_path) as test:
                      test.verify()
            except Exception:
                continue
            
            img = Image(
                image_path,
                width=4.5 * inch,
                height=3 * inch
            )     

            story.append(img)

            story.append(
                Spacer(
                    1,
                    10
                )
            )

            count += 1

            if count >= 10:
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
            "Background Information",
            styles["Heading1"]
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
                    5
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
            "Recent Developments",
            styles["Heading1"]
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
                "No recent developments found.",
                styles["BodyText"]
            )
        )

        return

    for index, article in enumerate(
        news,
        start=1
    ):

        title = article.get(
            "title",
            "Untitled"
        )

        story.append(
            paragraph(
                f"{index}. {title}",
                styles["Heading2"]
            )
        )

        meta = []

        if article.get("source"):
            meta.append(
                article["source"]
            )

        if article.get("published"):
            meta.append(
                article["published"]
            )

        if meta:

            story.append(
                paragraph(
                    " | ".join(meta),
                    styles["Meta"]
                )
            )

        full_text = (
            article.get("full_text")
            or article.get("summary")
            or ""
        )

        if full_text:

            story.append(
                paragraph(
                    full_text,
                    styles["BodyText"]
                )
            )

        story.append(
            Spacer(
                1,
                10
            )
        )

    story.append(
        PageBreak()
    )


def add_analysis_section(
    story,
    knowledge,
    styles
):

    story.append(
        paragraph(
            "Analysis",
            styles["Heading1"]
        )
    )

    add_rule(story)

    stats = knowledge.get(
        "statistics",
        {}
    )

    if stats:

        rows = [
            [
                "Metric",
                "Value"
            ]
        ]

        for key, value in stats.items():

            rows.append(
                [
                    str(key),
                    str(value)
                ]
            )

        table = Table(
            rows,
            colWidths=[
                3 * inch,
                2 * inch
            ]
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.black
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    )
                ]
            )
        )

        story.append(table)

    keywords = knowledge.get(
        "keywords",
        []
    )

    if keywords:

        story.append(
            Spacer(
                1,
                15
            )
        )

        story.append(
            paragraph(
                "Top Keywords",
                styles["Heading2"]
            )
        )

        bullet_items = []

        for word in keywords:

            bullet_items.append(
                ListItem(
                    paragraph(
                        word,
                        styles["BodyText"]
                    )
                )
            )

        story.append(
            ListFlowable(
                bullet_items,
                bulletType="bullet"
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

    refs = []

    wiki = knowledge.get(
        "wiki",
        {}
    )

    if wiki.get("url"):

        refs.append(
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
            refs.append(url)

    for article in knowledge.get(
        "articles",
        []
    ):

        url = article.get(
            "url"
        )

        if url:
            refs.append(url)

    refs = list(
        dict.fromkeys(refs)
    )

    bullets = []

    for ref in refs:

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
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch
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

    add_executive_summary(
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

    add_timeline(
        story,
        knowledge,
        styles
    )

    add_key_facts(
        story,
        knowledge,
        styles
    )

    add_recent_developments(
        story,
        knowledge,
        styles
    )

    add_analysis_section(
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