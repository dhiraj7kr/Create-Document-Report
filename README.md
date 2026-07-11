# Create Document Report (AI-Enhanced Edition)

## Overview

Create Document Report is an advanced, Python-based automated research pipeline. It collects information from multiple online sources, processes the data, downloads relevant images, builds a structured knowledge base, and now outputs both a **professional PDF report** and a **synthesized AI Markdown dossier**.

The project is designed to automatically create detailed dossiers for people, companies, technologies, products, events, or any topic available online.

Unlike traditional summarizers, this project performs full-stack research:

* Wikipedia research
* News aggregation
* Deep web crawling
* Article extraction
* Image collection
* Knowledge organization
* PDF generation
* **[NEW] Local AI Synthesis (via Ollama & Qwen2.5-Coder)**

---

## 🚀 What's New in this Version?

This iteration introduces a **Zero-Cost Local AI Pipeline**. Instead of just dumping scraped text into a PDF, the project now saves a raw `_knowledge.json` payload and passes it securely to a local instance of Ollama running `qwen2.5-coder:7b`.

The AI automatically deduplicates overlapping facts, cleans up scraped formatting, and synthesizes the raw data into a highly readable, professionally formatted Markdown file—all without requiring paid API keys or sending your research to the cloud.

---

## Features

### Multi-Source Research

* **Wikipedia:** Retrieves topic overviews, detailed sections, and historical backgrounds.
* **News Sources:** Collects the latest news articles and trending updates via RSS.
* **Web Crawling:** Discovers and traverses related URLs to expand the information pool beyond mainstream sources.
* **Image Collection:** Safely downloads topic-related images and article headers to build a visual gallery.

### Multi-Format Output

1. **PDF Report:** Contains an Executive Summary, Image Gallery, Background, Timeline, Key Facts, and References.
2. **Raw JSON Payload:** A highly structured data dump of everything the crawler found.
3. **AI Markdown Dossier:** A clean, deduplicated, and deeply synthesized text report.

---

## Project Architecture

```text
User Topic
    │
    ▼
Wikipedia Source
    │
    ▼
News Source
    │
    ▼
Crawler
    │
    ▼
Article Extractor
    │
    ▼
Image Crawler
    │
    ▼
Knowledge Builder
    │
    ├──► PDF Report Generator ────────► Generated PDF Report
    │
    └──► JSON Payload Export
            │
            └──► Local Ollama API ────► AI Markdown Dossier

```

---

## Project Structure

```text
Create-Document-Report
│
├── main.py
│
├── pdf
│   └── report_builder.py
│
├── sources
│   ├── wikipedia_source.py
│   ├── news_source.py
│   ├── crawler.py
│   ├── article_extractor.py
│   ├── image_crawler.py
│   └── knowledge_builder.py
│
├── images/
│
├── reports/
│   ├── Topic_Report.pdf
│   ├── Topic_knowledge.json
│   └── Topic_Final_AI_Report.md
│
├── requirements.txt
│
└── README.md

```

---

## Component Details

* **`main.py`**: Main entry point. Coordinates all modules, builds the knowledge base, generates the PDF, and triggers the local AI formatting pipeline.
* **`wikipedia_source.py`**: Extracts topic summaries, sections, and subsections from Wikipedia.
* **`news_source.py`**: Retrieves RSS feeds and extracts recent developments and news articles.
* **`crawler.py`**: Performs deep crawling for URL discovery and link traversal to expand available information.
* **`article_extractor.py`**: Uses Newspaper3k to extract full article text, authors, publish dates, and top images.
* **`image_crawler.py`**: Discovers and downloads valid images (JPG, PNG, WEBP), filtering out unsupported formats like SVGs.
* **`knowledge_builder.py`**: Combines all scraped content into a unified dictionary structure, generating timelines, facts, and statistics.
* **`report_builder.py`**: Uses ReportLab to generate the final 10-chapter PDF report.

---

## Installation & Setup

### 1. Local AI Setup (Required for Markdown Generation)

To use the AI synthesis feature, you must have Ollama installed and running on your machine.

1. Download [Ollama](https://ollama.com/).
2. Open your terminal and pull the required model:
```bash
ollama run qwen2.5-coder:7b

```


3. Keep the Ollama application running in the background.

### 2. Python Environment Setup

Create and activate a virtual environment:

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate

```

**Linux / Mac:**

```bash
python3 -m venv .venv
source .venv/bin/activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

---

## Usage

Run the main script from your terminal and pass the topic you want to research:

```bash
python main.py "Andrej Karpathy"

```

**Examples:**

```bash
python main.py "Tesla Robotics"
python main.py "OpenAI Sora"

```

### Advanced Arguments:

* `-o`, `--output-dir`: Specify a custom folder for reports.
* `--news-limit`: Limit the amount of news articles processed (default: 10).
* `--wiki-section-limit`: Limit Wikipedia sections scraped (default: 15).
* `--verbose`: Enable debug logging.

---

## Output

For a topic like "OpenAI", check the `reports/` folder. You will find:

1. **`OpenAI_Report.pdf`**: The standard, heavily illustrated visual dossier.
2. **`OpenAI_knowledge.json`**: The raw scraped data matrix.
3. **`OpenAI_Final_AI_Report.md`**: The AI-synthesized, deduplicated final text report.

---

## Error Handling

The project is built to be highly resilient:

* **Missing Pages:** Wikipedia failures are handled gracefully; the script moves on to news and crawling.
* **Invalid Images:** Corrupt or dead image links are skipped automatically.
* **Unsupported Formats:** SVG images are ignored to prevent PDF build crashes.
* **AI Timeouts:** If Ollama is offline or takes too long, the script will gracefully log a warning and still provide your PDF and JSON files.

---

## Future Improvements

* **Better Image Selection:** Face detection, duplicate removal, and AI-generated image captions.
* **Smarter Crawling:** Topic relevance scoring, domain filtering, and link prioritization.
* **More Sources:** Add support for ArXiv, GitHub, research papers, and SEC filings.
* **Better PDF Design:** Custom themes, charts, tables, and infographics.
* **Export Formats:** Support for DOCX, HTML, and PowerPoint.

---

## Technologies Used

* **Language:** Python
* **PDF Generation:** ReportLab
* **Web Scraping:** Newspaper3k, BeautifulSoup, Requests
* **Content Parsing:** FeedParser, Wikipedia API
* **Image Processing:** Pillow
* **AI Synthesis:** Ollama (qwen2.5-coder:7b)

---

## License

This project is intended for educational, research, and personal use. Always respect website terms of service and copyright regulations when collecting content from external sources.

---

## Author

**Dhiraj Kumar** *Automated Research Report Generator using Python, Web Crawling, Knowledge Extraction, PDF Generation, and Local AI Synthesis.*
