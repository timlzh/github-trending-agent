from typing import List

from feedgen.feed import FeedGenerator

from app.enums import AllowedDateRanges
from app.models import Developer, Repository


class RSSService:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def generate_repository_feed(
        self, repositories: List[Repository], since: AllowedDateRanges
    ) -> str:
        fg = FeedGenerator()
        fg.title(f"GitHub Trending Repositories ({since})")
        fg.description("AI summarized GitHub trending repositories")
        fg.link(href=self.base_url)
        fg.language("en")

        for repo in repositories:
            fe = fg.add_entry()
            fe.title(f"{repo.username}/{repo.repository_name}")
            fe.link(href=repo.url)
            fe.description(repo.ai_summary)
            fe.author({"name": repo.username})

        return fg.rss_str(pretty=True).decode("utf-8")

    def generate_developer_feed(self, developers: List[Developer], since: str) -> str:
        fg = FeedGenerator()
        fg.title(f"GitHub Trending Developers ({since})")
        fg.description("AI summarized GitHub trending developers")
        fg.link(href=self.base_url)
        fg.language("en")

        for dev in developers:
            fe = fg.add_entry()
            fe.title(f"{dev.name or dev.username}")
            fe.link(href=dev.url)
            fe.description(dev.ai_summary)
            fe.author({"name": dev.username})

        return fg.rss_str(pretty=True).decode("utf-8")
