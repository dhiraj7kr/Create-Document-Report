import argparse
import logging
import sys
from pathlib import Path

from sources.wikipedia_source import (
    get_wikipedia_content,
    WikipediaSourceError
)

from sources.news_source import (
    get_news,
    NewsSourceError
)

from sources.crawler import DeepCrawler
from sources.article_extractor import ArticleExtractor
from sources.image_crawler import ImageCrawler
from sources.knowledge_builder import KnowledgeBuilder

from pdf.report_builder import build_report


DEFAULT_NEWS_LIMIT = 10


def parse_args():

    parser = argparse.ArgumentParser(
        description="Advanced Research Report Generator"
    )

    parser.add_argument(
        "topic",
        nargs="?",
        help="Topic to research"
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="reports",
        help="Output folder"
    )

    parser.add_argument(
        "--news-limit",
        type=int,
        default=DEFAULT_NEWS_LIMIT
    )

    parser.add_argument(
        "--wiki-section-limit",
        type=int,
        default=15
    )

    parser.add_argument(
        "--verbose",
        action="store_true"
    )

    return parser.parse_args()


def configure_logging(verbose):

    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s"
    )


def read_topic(topic):

    value = topic or input(
        "Enter topic: "
    )

    value = value.strip()

    if len(value) < 2:
        raise ValueError(
            "Topic must contain at least 2 characters."
        )

    return value


def collect_seed_urls(
    wiki,
    news
):

    urls = []

    if wiki and wiki.get("url"):
        urls.append(
            wiki["url"]
        )

    for item in news:

        url = (
            item.get("article_url")
            or item.get("link")
        )

        if url:
            urls.append(url)

    return list(
        dict.fromkeys(urls)
    )


def main():

    args = parse_args()

    configure_logging(
        args.verbose
    )

    try:

        topic = read_topic(
            args.topic
        )

        output_dir = Path(
            args.output_dir
        )

        logging.info(
            "Collecting Wikipedia content..."
        )

        try:

            wiki = get_wikipedia_content(
                topic,
                section_limit=args.wiki_section_limit
            )

        except WikipediaSourceError:

            wiki = {}

        logging.info(
            "Collecting news..."
        )

        try:

            news = get_news(
                topic,
                limit=args.news_limit,
                include_article_content=True
            )

            # Keep only the most relevant news
            news = news[:5]

        except NewsSourceError:

            news = []

        logging.info(
            "Preparing crawler..."
        )

        crawler = DeepCrawler()

        seed_urls = collect_seed_urls(
            wiki,
            news
        )

        logging.info(
            "Crawling %s URLs...",
            len(seed_urls)
        )

        crawled_articles = crawler.crawl(
            seed_urls=seed_urls,
            max_pages=8
        )

        logging.info(
            "Extracting article data..."
        )

        extractor = ArticleExtractor()

        extracted_articles = []

        for article in crawled_articles:

            url = article.get("url")

            if not url:
                continue

            extracted = extractor.extract(
                url
            )

            if extracted.get("text"):
                extracted_articles.append(
                    extracted
                )

        # Keep the richest articles
        extracted_articles.sort(
            key=lambda x: len(
                x.get(
                    "text",
                    ""
                )
            ),
            reverse=True
        )

        extracted_articles = extracted_articles[:10]

        logging.info(
            "Downloading images..."
        )

        image_crawler = ImageCrawler()

        image_paths = []

        for article in extracted_articles:

            top_image = article.get(
                "top_image"
            )

            if top_image:

                path = (
                    image_crawler
                    .download_article_image(
                        top_image
                    )
                )

                if path:
                    image_paths.append(
                        path
                    )

        if wiki and wiki.get("url"):

            try:

                wiki_images = (
                    image_crawler
                    .download_page_images(
                        wiki["url"],
                        limit=5
                    )
                )

                image_paths.extend(
                    wiki_images
                )

            except Exception:
                pass

        image_paths = list(
            dict.fromkeys(
                image_paths
            )
        )

        # Keep only the best images
        image_paths = image_paths[:8]

        logging.info(
            "Building knowledge base..."
        )

        builder = KnowledgeBuilder()

        knowledge = builder.build(
            topic=topic,
            wiki_data=wiki,
            news_articles=news,
            crawled_articles=extracted_articles,
            image_paths=image_paths
        )

        knowledge["statistics"] = (
            builder.statistics(
                knowledge
            )
        )

        # Report metadata
        knowledge["report_metadata"] = {
            "topic": topic,
            "news_count": len(news),
            "article_count": len(
                extracted_articles
            ),
            "image_count": len(
                image_paths
            )
        }

        logging.info(
            "Knowledge Base Summary"
        )

        logging.info(
            "News Articles: %s",
            len(news)
        )

        logging.info(
            "Crawled Articles: %s",
            len(extracted_articles)
        )

        logging.info(
            "Images: %s",
            len(image_paths)
        )

        logging.info(
            "Generating PDF..."
        )

        report_path = build_report(
            topic=topic,
            knowledge=knowledge,
            output_dir=output_dir
        )

        print()
        print("=" * 60)
        print(
            "REPORT GENERATED SUCCESSFULLY"
        )
        print("=" * 60)
        print(report_path)
        print("=" * 60)

        return 0

    except KeyboardInterrupt:

        logging.error(
            "Process cancelled."
        )

        return 130

    except Exception:

        logging.exception(
            "Unexpected error."
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())