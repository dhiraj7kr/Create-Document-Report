import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from newspaper import Article

USER_AGENT = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}


class DeepCrawler:

    def __init__(self):
        self.visited = set()

    def extract_article(self, url):
        try:
            article = Article(url)
            article.download()
            article.parse()

            return {
                "title": article.title,
                "text": article.text,
                "image": article.top_image,
                "authors": article.authors,
                "publish_date": str(article.publish_date)
                if article.publish_date
                else "",
                "url": url,
            }

        except Exception:
            return None

    def extract_links(self, url):
        links = []

        try:
            response = requests.get(
                url,
                timeout=20,
                headers=USER_AGENT
            )

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            for tag in soup.find_all("a", href=True):

                href = tag["href"]

                full_url = urljoin(
                    url,
                    href
                )

                if full_url.startswith("http"):
                    links.append(full_url)

        except Exception:
            pass

        return list(set(links))

    def crawl(self, seed_urls, max_pages=15):

        articles = []

        queue = list(seed_urls)

        while queue and len(self.visited) < max_pages:

            url = queue.pop(0)

            if url in self.visited:
                continue

            self.visited.add(url)

            article = self.extract_article(url)

            if article:
                articles.append(article)

            try:
                discovered = self.extract_links(url)

                for link in discovered:

                    if link not in self.visited:
                        queue.append(link)

            except Exception:
                pass

        return articles