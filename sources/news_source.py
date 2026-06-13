import json
import re
from datetime import datetime
from html import unescape
from urllib.parse import quote, quote_plus, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup


class NewsSourceError(RuntimeError):
    """Raised when the news source cannot be reached or parsed."""


ARTICLE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0 Safari/537.36 ResearchReportGenerator/2.0"
)
MAX_ARTICLE_CHARS = 9000


def _clean_text(value):
    raw = str(value or "")
    if "<" in raw or "&" in raw:
        text = BeautifulSoup(raw, "html.parser").get_text(" ")
    else:
        text = raw
    return " ".join(unescape(text).split())


def _entry_date(entry):
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed:
        return ""
    return datetime(*parsed[:6]).strftime("%Y-%m-%d")


def _google_news_article_id(url):
    parsed = urlparse(url)
    if "news.google.com" not in parsed.netloc or "/articles/" not in parsed.path:
        return ""
    return parsed.path.rsplit("/articles/", 1)[-1].strip("/")


def _decode_google_news_url(url, timeout):
    article_id = _google_news_article_id(url)
    if not article_id:
        return url

    try:
        session = requests.Session()
        page = session.get(
            f"https://news.google.com/articles/{article_id}",
            timeout=timeout,
            headers={"User-Agent": ARTICLE_USER_AGENT},
        )
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        decode_data = soup.find(attrs={"data-n-a-sg": True})
        if not decode_data:
            return url

        timestamp = decode_data.get("data-n-a-ts")
        signature = decode_data.get("data-n-a-sg")
        if not timestamp or not signature:
            return url

        inner = (
            '["garturlreq",[['
            '"en-US","US",["FINANCE_TOP_INDICES","WEB_TEST_1_0_0"],null,null,1,1,'
            '"US:en",null,180,null,null,null,null,null,0,null,null,[1608992183,723341000]],'
            '"en-US","US",1,[2,3,4,8],1,0,"655000234",0,0,null,0],'
            f'"{article_id}",{timestamp},"{signature}"]'
        )
        request_body = f'[[["Fbv4je","{inner.replace(chr(34), chr(92) + chr(34))}",null,"generic"]]]'
        response = session.post(
            "https://news.google.com/_/DotsSplashUi/data/batchexecute?rpcids=Fbv4je",
            data=f"f.req={quote(request_body)}",
            timeout=timeout,
            headers={
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "User-Agent": ARTICLE_USER_AGENT,
            },
        )
        response.raise_for_status()

        for candidate in re.findall(r"https?://[^\\\"]+", response.text):
            if "news.google.com" not in urlparse(candidate).netloc:
                return candidate
    except requests.RequestException:
        return url

    return url


def _canonical_url(soup, fallback):
    tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    if tag and tag.get("href"):
        return tag["href"]
    tag = soup.find("meta", property="og:url")
    if tag and tag.get("content"):
        return tag["content"]
    return fallback


def _page_title(soup):
    for selector in [
        ("meta", {"property": "og:title"}),
        ("meta", {"name": "twitter:title"}),
    ]:
        tag = soup.find(*selector)
        if tag and tag.get("content"):
            return _clean_text(tag["content"])
    if soup.title and soup.title.string:
        return _clean_text(soup.title.string)
    return ""


def _is_useful_paragraph(text):
    if len(text) < 70:
        return False
    lowered = text.lower()
    blocked = [
        "accept cookies",
        "advertisement",
        "all rights reserved",
        "enable javascript",
        "privacy policy",
        "sign up",
        "subscribe",
    ]
    return not any(item in lowered for item in blocked)


def _extract_paragraphs(soup):
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    containers = soup.find_all("article")
    if not containers:
        containers = soup.find_all("main")
    if not containers:
        containers = [soup.body or soup]

    paragraphs = []
    seen = set()
    for container in containers:
        for paragraph in container.find_all("p"):
            text = _clean_text(paragraph.get_text(" "))
            fingerprint = text.lower()
            if fingerprint in seen or not _is_useful_paragraph(text):
                continue
            seen.add(fingerprint)
            paragraphs.append(text)

            if sum(len(item) for item in paragraphs) >= MAX_ARTICLE_CHARS:
                return paragraphs

    return paragraphs


def _json_ld_nodes(value):
    if isinstance(value, dict):
        yield value
        for key in ("@graph", "itemListElement"):
            child = value.get(key)
            if child:
                yield from _json_ld_nodes(child)
    elif isinstance(value, list):
        for item in value:
            yield from _json_ld_nodes(item)


def _extract_structured_text(soup):
    candidates = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        for node in _json_ld_nodes(data):
            body = node.get("articleBody") or node.get("description")
            if isinstance(body, str) and _is_useful_paragraph(_clean_text(body)):
                candidates.append(_clean_text(body))

    for attrs in [
        {"property": "og:description"},
        {"name": "description"},
        {"name": "twitter:description"},
    ]:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            text = _clean_text(tag["content"])
            if _is_useful_paragraph(text):
                candidates.append(text)

    seen = set()
    unique = []
    for text in candidates:
        fingerprint = text.lower()
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(text)
    return "\n\n".join(unique)


def _fetch_article_content(url, timeout):
    resolved_url = _decode_google_news_url(url, timeout=timeout)
    empty_result = {
        "article_url": resolved_url,
        "article_title": "",
        "full_text": "",
        "content_status": "Article text was not available from the publisher page.",
    }

    try:
        response = requests.get(
            resolved_url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": ARTICLE_USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException:
        return {
            **empty_result,
            "content_status": "Article text could not be fetched from the publisher page.",
        }

    content_type = response.headers.get("content-type", "").lower()
    if "html" not in content_type and "text" not in content_type:
        return empty_result

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = _extract_paragraphs(soup)
    full_text = "\n\n".join(paragraphs) or _extract_structured_text(soup)
    if len(full_text) > MAX_ARTICLE_CHARS:
        full_text = full_text[:MAX_ARTICLE_CHARS].rsplit(" ", 1)[0]

    return {
        "article_url": _canonical_url(soup, response.url),
        "article_title": _page_title(soup),
        "full_text": full_text,
        "content_status": "Article text extracted." if full_text else empty_result["content_status"],
    }


def get_news(topic, limit=8, timeout=15, include_article_content=True, article_timeout=12):
    """Return recent news results for a topic from Google News RSS."""
    if not topic or not topic.strip():
        raise ValueError("Topic is required to fetch news.")

    if limit <= 0:
        return []

    query = quote_plus(topic.strip())
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "ResearchReportGenerator/2.0"},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise NewsSourceError("Unable to fetch the news feed. Please try again later.") from exc

    feed = feedparser.parse(response.content)

    if getattr(feed, "bozo", False):
        raise NewsSourceError("Unable to parse the news feed. Please try again later.")

    results = []
    seen_links = set()
    for entry in feed.entries:
        link = _clean_text(getattr(entry, "link", ""))
        if not link or link in seen_links:
            continue

        seen_links.add(link)
        item = {
            "title": _clean_text(getattr(entry, "title", "")) or "Untitled news item",
            "link": link,
            "published": _entry_date(entry),
            "source": _clean_text(getattr(getattr(entry, "source", None), "title", "")),
            "summary": _clean_text(getattr(entry, "summary", "")),
            "article_url": link,
            "article_title": "",
            "full_text": "",
            "content_status": "Article content fetch was disabled.",
        }
        if include_article_content:
            item.update(_fetch_article_content(link, timeout=article_timeout))

        results.append(item)

        if len(results) >= limit:
            break

    return results
