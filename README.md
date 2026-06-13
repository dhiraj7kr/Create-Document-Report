# Create Document Report

## Overview

Create Document Report is a Python-based automated research report generator that collects information from multiple online sources, processes the data, downloads relevant images, builds a structured knowledge base, and generates a professional PDF report.

The project is designed to automatically create detailed reports for people, companies, technologies, products, events, or any topic available online.

Unlike traditional summarizers, this project performs:

* Wikipedia research
* News aggregation
* Web crawling
* Article extraction
* Image collection
* Knowledge organization
* PDF generation

The final output is a well-structured PDF report containing:

* Executive Summary
* Background Information
* Timeline
* Key Facts
* Recent Developments
* Analysis
* References
* Images

---

# Features

## Multi-Source Research

The system collects information from multiple sources:

### Wikipedia

Retrieves:

* Topic overview
* Detailed sections
* Historical information
* Background knowledge

### News Sources

Collects:

* Latest news articles
* Recent developments
* Trending updates

### Web Crawling

The crawler visits multiple pages and extracts:

* Related articles
* Additional information
* Supporting content

### Image Collection

Downloads:

* Topic-related images
* Article images
* Reference images

These images are later inserted into the generated PDF.

---

# Project Architecture

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
    ▼
PDF Report Generator
    │
    ▼
Generated PDF
```

---

# Project Structure

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
├── images
│
├── reports
│
├── requirements.txt
│
└── README.md
```

---

# Component Details

## main.py

Main entry point of the application.

Responsibilities:

* Reads user topic
* Starts data collection
* Coordinates all modules
* Builds knowledge base
* Generates final PDF

---

## wikipedia_source.py

Responsible for collecting Wikipedia information.

Extracts:

* Topic summary
* Sections
* Subsections
* Page URL

Example:

```python
wiki = get_wikipedia_content("Andrej Karpathy")
```

---

## news_source.py

Responsible for collecting news articles.

Features:

* RSS feed retrieval
* News article extraction
* Recent developments

Returns:

```python
[
    {
        "title": "...",
        "summary": "...",
        "url": "..."
    }
]
```

---

## crawler.py

Performs deep crawling.

Features:

* URL discovery
* Related page extraction
* Link traversal
* Content collection

The crawler expands the amount of information available beyond Wikipedia and news sources.

---

## article_extractor.py

Uses Newspaper3k to extract:

* Full article text
* Authors
* Publish dates
* Keywords
* Top image

Example:

```python
extractor.extract(url)
```

Returns:

```python
{
    "title": "...",
    "text": "...",
    "summary": "...",
    "top_image": "..."
}
```

---

## image_crawler.py

Responsible for:

* Discovering images
* Downloading images
* Filtering invalid formats
* Removing unsupported SVG files

Supported formats:

* JPG
* JPEG
* PNG
* WEBP

Downloaded images are stored inside:

```text
images/
```

---

## knowledge_builder.py

Creates a structured knowledge base.

Combines:

* Wikipedia content
* News articles
* Crawled articles
* Images

Also generates:

* Keywords
* Timeline
* Facts
* Statistics

Example:

```python
knowledge = builder.build(...)
```

---

## report_builder.py

Generates the final PDF report.

Sections:

1. Cover Page
2. Contents
3. Executive Summary
4. Image Gallery
5. Background Information
6. Timeline
7. Key Facts
8. Recent Developments
9. Analysis
10. References

Uses:

* ReportLab
* Pillow

Output:

```text
reports/Topic_Report.pdf
```

---

# Installation

## Create Virtual Environment

```bash
python -m venv .venv
```

Activate:

### Windows

```bash
.venv\Scripts\activate
```

### Linux / Mac

```bash
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Requirements

```txt
reportlab
wikipedia-api
requests
beautifulsoup4
feedparser
pillow
newspaper3k
lxml
lxml_html_clean
python-dateutil
tldextract
cssselect
feedfinder2
jieba3k
```

---

# Usage

Generate a report:

```bash
python main.py "Andrej Karpathy"
```

Example:

```bash
python main.py "Tesla"
```

Example:

```bash
python main.py "OpenAI"
```

---

# Output

Example generated file:

```text
reports/
└── Andrej_Karpathy_Report.pdf
```

The report contains:

* Research information
* Images
* Timeline
* News analysis
* References

---

# Error Handling

The project handles:

### Missing Pages

Wikipedia failures are handled gracefully.

### Invalid Images

Corrupt images are skipped automatically.

### Unsupported Formats

SVG images are ignored.

### Network Failures

Failed requests do not terminate the application.

---

# Future Improvements

Potential enhancements:

## Better Image Selection

* Face detection
* Duplicate removal
* Image captions

## Smarter Crawling

* Topic relevance scoring
* Domain filtering
* Link prioritization

## More Sources

Add support for:

* ArXiv
* GitHub
* Company websites
* Research papers

## Better PDF Design

* Custom themes
* Charts
* Tables
* Infographics

## Export Formats

Support:

* DOCX
* HTML
* Markdown
* PowerPoint

---

# Technologies Used

Python

Libraries:

* ReportLab
* Newspaper3k
* BeautifulSoup
* Requests
* Pillow
* FeedParser
* Wikipedia API

---

# License

This project is intended for educational, research, and personal use.

Always respect website terms of service and copyright regulations when collecting content from external sources.

---

# Author

Dhiraj Kumar

Automated Research Report Generator using Python, Web Crawling, Knowledge Extraction, and PDF Generation.
