import wikipediaapi


class WikipediaSourceError(RuntimeError):
    """Raised when Wikipedia cannot be reached or parsed."""


def _section_to_dict(section, depth=0, max_depth=1):
    if depth > max_depth:
        return None

    text = " ".join((section.text or "").split())
    children = [
        child
        for child in (_section_to_dict(item, depth + 1, max_depth) for item in section.sections)
        if child
    ]

    if not text and not children:
        return None

    return {
        "title": section.title,
        "text": text,
        "children": children,
    }


def get_wikipedia_content(topic, section_limit=8):
    """Return summary and high-value sections from Wikipedia for a topic."""
    if not topic or not topic.strip():
        raise ValueError("Topic is required to fetch Wikipedia content.")

    try:
        wiki = wikipediaapi.Wikipedia(user_agent="ResearchReportGenerator/2.0", language="en")
        page = wiki.page(topic.strip())

        if not page.exists():
            return {}

        sections = []
        for section in page.sections:
            section_data = _section_to_dict(section)
            if section_data:
                sections.append(section_data)
            if len(sections) >= section_limit:
                break

        return {
            "title": page.title,
            "summary": " ".join((page.summary or "").split()),
            "url": page.fullurl,
            "sections": sections,
        }
    except Exception as exc:
        raise WikipediaSourceError("Unable to contact Wikipedia. Please try again later.") from exc
