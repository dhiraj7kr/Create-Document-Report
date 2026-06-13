import os
import uuid
import requests

from urllib.parse import urlparse
from bs4 import BeautifulSoup

IMAGE_DIR = "images"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}


class ImageCrawler:

    def __init__(self, image_dir=IMAGE_DIR):

        self.image_dir = image_dir

        os.makedirs(
            self.image_dir,
            exist_ok=True
        )

    def download_image(self, image_url):

        try:

            response = requests.get(
                image_url,
                headers=HEADERS,
                timeout=20,
                stream=True
            )

            if response.status_code != 200:
                return None

            content_type = response.headers.get(
                "Content-Type",
                ""
            ).lower()

            if "svg" in content_type:
                return None

            valid_types = [
                "jpeg",
                "jpg",
                "png",
                "webp"
            ]

            if not any(
                img_type in content_type
                for img_type in valid_types
            ):
                return None

            ext = image_url.split(".")[-1].lower()

            ext = ext.split("?")[0]

            if ext not in [
                "jpg",
                "jpeg",
                "png",
                "webp"
            ]:
                ext = "jpg"

            filename = (
                str(uuid.uuid4())
                + "."
                + ext
            )

            filepath = os.path.join(
                self.image_dir,
                filename
            )

            with open(filepath, "wb") as file:

                for chunk in response.iter_content(
                    chunk_size=8192
                ):

                    if chunk:
                        file.write(chunk)

            return filepath

        except Exception:
            return None

    def extract_images_from_page(
        self,
        url
    ):

        images = []

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=20
            )

            if response.status_code != 200:
                return images

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            for img in soup.find_all("img"):

                src = img.get("src")

                if not src:
                    continue

                if src.startswith("//"):
                    src = "https:" + src

                elif src.startswith("/"):

                    parsed = urlparse(url)

                    src = (
                        parsed.scheme
                        + "://"
                        + parsed.netloc
                        + src
                    )

                if not src.startswith("http"):
                    continue

                lower = src.lower()

                if (
                    ".svg" in lower
                    or "logo" in lower
                    or "icon" in lower
                ):
                    continue

                allowed = (
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp"
                )

                if any(
                    ext in lower
                    for ext in allowed
                ):
                    images.append(src)

        except Exception:
            pass

        return list(
            dict.fromkeys(images)
        )

    def download_page_images(
        self,
        url,
        limit=5
    ):

        image_urls = self.extract_images_from_page(
            url
        )

        downloaded = []

        for image_url in image_urls[:limit]:

            path = self.download_image(
                image_url
            )

            if path:
                downloaded.append(path)

        return downloaded

    def download_article_image(
        self,
        image_url
    ):

        if not image_url:
            return None

        return self.download_image(
            image_url
        )