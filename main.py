import argparse
import logging
import sys
import json
import requests
import re
from pathlib import Path

def run_local_ai_formatting(json_payload_path, topic):
    """
    Sends the generated knowledge JSON to the active local Ollama instance
    for deduplication and structured formatting.
    """
    logging.info("Initializing local AI optimization via Qwen2.5-Coder...")
    
    try:
        with open(json_payload_path, "r", encoding="utf-8") as f:
            knowledge = json.load(f)
    except Exception as e:
        logging.error("Failed to read JSON payload: %s", str(e))
        return

    # Directives to ensure formatting cleanliness and zero data repetition
    system_prompt = (
        "You are an expert analytical researcher and legal annotator. "
        "Review the provided JSON dataset containing Wikipedia extracts, news events, and crawled web articles. "
        "Consolidate and synthesize this data into a highly structured, dense, and clean Markdown dossier. "
        "CRITICAL: Identify and eliminate all duplicate facts, overlapping news stories, or repeating paragraphs. "
        "Organize the output into clear sections using professional Markdown headings."
    )
    
    user_prompt = f"Topic Focus: {topic}\n\nRaw Knowledge Dataset:\n{json.dumps(knowledge, indent=2)}"
    
    ollama_url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5-coder:7b",
        "prompt": f"{system_prompt}\n\n{user_prompt}",
        "stream": False
    }
    
    try:
        # 120-second timeout to accommodate processing large text inputs on local hardware
        response = requests.post(ollama_url, json=payload, timeout=120)
        response.raise_for_status()
        
        ai_response = response.json().get("response", "")
        
        # Save the finalized, deduplicated report
        output_path = json_payload_path.parent / f"{json_payload_path.stem}_Final_AI_Report.md"
        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write(ai_response)
            
        logging.info("Optimized AI Markdown report successfully saved to: %s", output_path)
        
    except requests.exceptions.ConnectionError:
        logging.error("Connection failed. Ensure Ollama is running in your system tray or background.")
    except Exception as e:
        logging.error("An error occurred during local LLM execution: %s", str(e))


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
                limit=args.news_limit,  # Let the CLI argument control this (default is 10)
                include_article_content=True
            )

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
            max_pages=30  # Increased for deeper data gathering
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
            key=lambda x: len(x.get("text", "")),
            reverse=True
        )

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
            "Generating PDF and Base JSON..."
        )

        report_path = build_report(
            topic=topic,
            knowledge=knowledge,
            output_dir=output_dir
        )
        
        # --- NEW: Trigger the local Ollama refinement pipeline ---
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", topic)[:100]
        json_file_path = output_dir / f"{safe_name}_knowledge.json"
        
        if json_file_path.exists():
            run_local_ai_formatting(json_file_path, topic)
        else:
            logging.warning("Skipping AI formatting; raw JSON knowledge base was not located.")
        # ---------------------------------------------------------

        print()
        print("=" * 60)
        print(
            "REPORT GENERATED SUCCESSFULLY"
        )
        print("=" * 60)
        print(f"PDF Location: {report_path}")
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