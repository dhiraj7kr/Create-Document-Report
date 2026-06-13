import argparse
import logging
import sys
from pathlib import Path

from pdf.report_builder import build_report
from sources.news_source import NewsSourceError, get_news
from sources.wikipedia_source import WikipediaSourceError, get_wikipedia_content


DEFAULT_NEWS_LIMIT = 8


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a detailed PDF research report for any topic."
    )
    parser.add_argument(
        "topic",
        nargs="?",
        help="Topic to research. If omitted, you will be prompted for it.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="reports",
        help="Directory where the PDF report will be saved. Default: reports",
    )
    parser.add_argument(
        "--news-limit",
        type=int,
        default=DEFAULT_NEWS_LIMIT,
        help=f"Maximum number of news items to include. Default: {DEFAULT_NEWS_LIMIT}",
    )
    parser.add_argument(
        "--wiki-section-limit",
        type=int,
        default=12,
        help="Maximum number of Wikipedia sections to include. Default: 12",
    )
    parser.add_argument(
        "--no-article-content",
        action="store_true",
        help="Skip fetching full article text from news links.",
    )
    parser.add_argument(
        "--article-timeout",
        type=int,
        default=12,
        help="Timeout in seconds for each article content request. Default: 12",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress and diagnostic logging.",
    )
    return parser.parse_args()


def configure_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )
    if not verbose:
        logging.getLogger("wikipediaapi").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def read_topic(topic):
    value = topic or input("Enter topic: ")
    value = value.strip()
    if len(value) < 2:
        raise ValueError("Please provide a topic with at least 2 characters.")
    return value


def main():
    args = parse_args()
    configure_logging(args.verbose)

    try:
        topic = read_topic(args.topic)
        news_limit = max(0, args.news_limit)
        output_dir = Path(args.output_dir)

        source_errors = []

        logging.info("Collecting Wikipedia context for '%s'...", topic)
        try:
            wiki = get_wikipedia_content(topic, section_limit=max(1, args.wiki_section_limit))
        except WikipediaSourceError as exc:
            wiki = {}
            source_errors.append(f"Wikipedia: {exc}")
            logging.warning("%s", exc)

        logging.info("Collecting current news for '%s'...", topic)
        try:
            news = get_news(
                topic,
                limit=news_limit,
                include_article_content=not args.no_article_content,
                article_timeout=max(3, args.article_timeout),
            )
        except NewsSourceError as exc:
            news = []
            source_errors.append(f"News: {exc}")
            logging.warning("%s", exc)

        if not wiki and not news:
            logging.warning(
                "No live sources returned content. The report will still include a source-status section."
            )

        logging.info("Building PDF report...")
        report_path = build_report(
            topic=topic,
            wiki=wiki,
            news=news,
            output_dir=output_dir,
            source_errors=source_errors,
        )
        print(f"Report generated: {report_path}")
        return 0

    except ValueError as exc:
        logging.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        logging.error("Report generation cancelled.")
        return 130
    except Exception:
        logging.exception("Unexpected error while generating the report.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
