from newspaper import Article
from newspaper import Config
from datetime import datetime


class ArticleExtractor:

    def __init__(self):

        self.config = Config()

        self.config.browser_user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        )

        self.config.request_timeout = 20

    def extract(self, url):

        try:

            article = Article(
                url,
                config=self.config
            )

            article.download()
            article.parse()
            article.nlp()

            return {
                "title": article.title,
                "text": article.text,
                "summary": article.summary,
                "keywords": article.keywords,
                "authors": article.authors,
                "top_image": article.top_image,
                "publish_date": self._format_date(
                    article.publish_date
                ),
                "url": url
            }

        except Exception as e:

            return {
                "title": "",
                "text": "",
                "summary": "",
                "keywords": [],
                "authors": [],
                "top_image": "",
                "publish_date": "",
                "url": url,
                "error": str(e)
            }

    def _format_date(self, value):

        if not value:
            return ""

        if isinstance(value, datetime):
            return value.strftime(
                "%Y-%m-%d"
            )

        return str(value)

    def extract_multiple(
        self,
        urls
    ):

        results = []

        for url in urls:

            data = self.extract(url)

            if data.get("text"):
                results.append(data)

        return results