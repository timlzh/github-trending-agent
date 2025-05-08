import asyncio
from typing import List

from app.enums import (
    AllowedDateRanges,
    AllowedProgrammingLanguages,
    AllowedSpokenLanguages,
)
from app.models import Developer, Repository
from app.services.scraping import (
    filter_articles,
    get_request,
    make_soup,
    scraping_developers,
    scraping_repositories,
)


class GitHubTrendingService:
    BASE_URL = "https://github.com/trending"

    async def get_trending_repositories(
        self,
        since: AllowedDateRanges | None = None,
        spoken_language: AllowedSpokenLanguages | None = None,
        language: AllowedProgrammingLanguages | None = None,
    ) -> List[Repository]:
        """Returns data about trending repositories (all programming
        languages, cannot be specified on this endpoint).
        """
        payload = {"since": "daily"}
        if since:
            payload["since"] = since.value
        if spoken_language:
            payload["spoken_language_code"] = spoken_language.value

        url = "https://github.com/trending"
        if language:
            url = f"{url}/{language.value}"

        sem = asyncio.Semaphore()
        async with sem:
            raw_html = await get_request(url, compress=True, params=payload)
        if not isinstance(raw_html, str):
            return []

        articles_html = filter_articles(raw_html)
        soup = make_soup(articles_html)
        return scraping_repositories(soup)

    async def get_trending_developers(
        self,
        since: AllowedDateRanges | None = None,
        language: AllowedProgrammingLanguages | None = None,
    ) -> List[Developer]:
        """Returns data about trending developers. A specific programming
        language can be added as path parameter to specify search.
        """
        payload = {"since": "daily"}
        if since:
            payload["since"] = since.value

        url = "https://github.com/trending/developers"
        if language:
            url = f"{url}/{language.value}"
        sem = asyncio.Semaphore()
        async with sem:
            raw_html = await get_request(url, compress=True, params=payload)
        if not isinstance(raw_html, str):
            return []

        articles_html = filter_articles(raw_html)
        soup = make_soup(articles_html)
        return scraping_developers(soup)


if __name__ == "__main__":

    async def main():
        github_service = GitHubTrendingService()
        print(
            await github_service.get_trending_repositories(
                since=AllowedDateRanges.daily,
            )
        )

    asyncio.run(main())
