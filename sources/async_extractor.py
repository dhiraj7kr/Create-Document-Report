import asyncio
import aiohttp
import logging
from newspaper import Article

# Standard browser headers to avoid blocks
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}

async def fetch_html(session, url):
    """Asynchronously downloads the HTML content of a webpage."""
    try:
        async with session.get(url, headers=HEADERS, timeout=15) as response:
            if response.status == 200:
                return url, await response.text()
            return url, None
    except Exception:
        return url, None

def extract_article_data(url, html):
    """Synchronous CPU-bound task using newspaper3k."""
    if not html:
        return None
        
    try:
        article = Article(url)
        article.set_html(html) # Inject the downloaded HTML
        article.parse()
        
        return {
            "title": article.title,
            "text": article.text,
            "top_image": article.top_image,
            "authors": article.authors,
            "publish_date": str(article.publish_date) if article.publish_date else "",
            "url": url,
        }
    except Exception:
        return None

async def process_urls_concurrently(urls):
    """
    Takes a list of URLs, fetches them all at exactly the same time,
    and extracts their data cleanly.
    """
    logging.info("Starting async extraction for %s URLs...", len(urls))
    results = []
    
    # Open a single concurrent session
    async with aiohttp.ClientSession() as session:
        # Create a massive batch of download tasks
        download_tasks = [fetch_html(session, url) for url in urls]
        
        # Run all downloads simultaneously
        downloaded_pages = await asyncio.gather(*download_tasks)
        
        # Parse the downloaded HTML (pushing CPU work to separate threads)
        parse_tasks = []
        for url, html in downloaded_pages:
            if html:
                # asyncio.to_thread prevents newspaper3k from freezing the async loop
                task = asyncio.to_thread(extract_article_data, url, html)
                parse_tasks.append(task)
                
        # Gather all extracted data
        extracted_data = await asyncio.gather(*parse_tasks)
        
        # Filter out failed extractions
        for data in extracted_data:
            if data and data.get("text"):
                results.append(data)
                
    return results

# Wrapper to call from your synchronous main.py
def run_fast_extraction(urls):
    return asyncio.run(process_urls_concurrently(urls))