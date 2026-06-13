from collections import Counter
import re


class KnowledgeBuilder:

    def __init__(self):
        pass

    def build(
        self,
        topic,
        wiki_data,
        news_articles,
        crawled_articles,
        image_paths
    ):

        all_text = []

        if wiki_data:

            all_text.append(
                wiki_data.get(
                    "summary",
                    ""
                )
            )

            for section in wiki_data.get(
                "sections",
                []
            ):

                all_text.append(
                    section.get(
                        "text",
                        ""
                    )
                )

        for article in news_articles:

            all_text.append(
                article.get(
                    "full_text",
                    ""
                )
            )

            all_text.append(
                article.get(
                    "summary",
                    ""
                )
            )

        for article in crawled_articles:

            all_text.append(
                article.get(
                    "text",
                    ""
                )
            )

            all_text.append(
                article.get(
                    "summary",
                    ""
                )
            )

        combined_text = "\n\n".join(
            all_text
        )

        return {
            "topic": topic,
            "wiki": wiki_data,
            "news": news_articles,
            "articles": crawled_articles,
            "images": image_paths,
            "keywords": self.extract_keywords(
                combined_text
            ),
            "timeline": self.extract_timeline(
                combined_text
            ),
            "facts": self.extract_facts(
                combined_text
            ),
            "full_text": combined_text
        }

    def extract_keywords(
        self,
        text,
        limit=20
    ):

        stopwords = {
            "the",
            "and",
            "that",
            "with",
            "from",
            "this",
            "have",
            "been",
            "they",
            "their",
            "about",
            "which",
            "into",
            "after",
            "also",
            "were",
            "while",
            "would",
            "there",
            "other"
        }

        words = re.findall(
            r"\b[a-zA-Z]{4,}\b",
            text.lower()
        )

        filtered = [
            word
            for word in words
            if word not in stopwords
        ]

        counts = Counter(
            filtered
        )

        return [
            word
            for word, _
            in counts.most_common(limit)
        ]

    def extract_timeline(
        self,
        text
    ):

        years = re.findall(
            r"\b(19\d{2}|20\d{2})\b",
            text
        )

        counts = Counter(
            years
        )

        timeline = []

        for year, count in sorted(
            counts.items()
        ):

            timeline.append(
                {
                    "year": year,
                    "mentions": count
                }
            )

        return timeline

    def extract_facts(
        self,
        text,
        max_facts=40
    ):

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text
        )

        facts = []

        for sentence in sentences:

            sentence = sentence.strip()

            if len(sentence) < 60:
                continue

            if len(sentence) > 400:
                continue

            facts.append(
                sentence
            )

            if len(facts) >= max_facts:
                break

        return facts

    def statistics(
        self,
        knowledge
    ):

        return {
            "articles":
                len(
                    knowledge.get(
                        "articles",
                        []
                    )
                ),

            "news":
                len(
                    knowledge.get(
                        "news",
                        []
                    )
                ),

            "images":
                len(
                    knowledge.get(
                        "images",
                        []
                    )
                ),

            "keywords":
                len(
                    knowledge.get(
                        "keywords",
                        []
                    )
                ),

            "facts":
                len(
                    knowledge.get(
                        "facts",
                        []
                    )
                ),

            "characters":
                len(
                    knowledge.get(
                        "full_text",
                        ""
                    )
                )
        }