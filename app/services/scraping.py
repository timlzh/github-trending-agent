"""Scraping
===================
Functions to scrape repository/developer data (HTML -> list of dicts).
"""

# Copyright (c) 2021, Niklas Tiede.
# All rights reserved. Distributed under the MIT License.
from typing import Any, Dict, List, Optional, Union

import aiohttp
import bs4

from app.models import Developer, Repository


async def get_request(
    url: str,  # Explicitly take url as a string
    *,  # Mark subsequent arguments as keyword-only
    params: Optional[Dict[str, str]] = None,
    compress: Optional[bool] = None,
    **other_kwargs: Any  # For any other keyword arguments aiohttp.get might take
) -> Union[str, aiohttp.ClientConnectorError]:
    """Asynchronous GET request with aiohttp."""
    try:
        # Prepare the keyword arguments for session.get
        request_kwargs = {}
        if params is not None:
            request_kwargs["params"] = params
        if compress is not None:
            request_kwargs["compress"] = compress
        request_kwargs.update(other_kwargs)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, **request_kwargs) as resp:  # Pass url directly
                return await resp.text()
    except aiohttp.ClientConnectorError as cce:
        return cce


def filter_articles(raw_html: str) -> str:
    """Filters HTML out, which is not enclosed by article-tags.
    Beautifulsoup is inaccurate and slow when applied on a larger
    HTML string, this filtration fixes this.
    """
    raw_html_lst = raw_html.split("\n")

    # count number of article tags within the document (varies from 0 to 50):
    article_tags_count = 0
    tag = "article"
    for line in raw_html_lst:
        if tag in line:
            article_tags_count += 1

    # copy HTML enclosed by first and last article-tag:
    articles_arrays, is_article = [], False
    for line in raw_html_lst:
        if tag in line:
            article_tags_count -= 1
            is_article = True
        if is_article:
            articles_arrays.append(line)
        if not article_tags_count:
            is_article = False
    return "".join(articles_arrays)


def make_soup(articles_html: str) -> bs4.element.ResultSet:
    """HTML enclosed by article-tags is converted into a
    soup for further data extraction.
    """
    soup = bs4.BeautifulSoup(articles_html, "lxml")
    return soup.find_all("article", class_="Box-row")


def scraping_repositories(
    matches: bs4.element.ResultSet,
) -> List[Repository]:
    """Data about all trending repositories are extracted."""
    trending_repositories = []
    for rank, match in enumerate(matches):
        # description
        if match.p:
            description = match.p.get_text(strip=True)
        else:
            description = None

        # relative url
        rel_url = match.h2.a["href"]

        # absolute url:
        repo_url = "https://github.com" + rel_url

        # name of repo
        repository_name = rel_url.split("/")[-1]

        # author (username):
        username = rel_url.split("/")[-2]

        # language and color
        progr_language = match.find("span", itemprop="programmingLanguage")
        if progr_language:
            language = progr_language.get_text(strip=True)
            lang_color_tag = match.find("span", class_="repo-language-color")
            lang_color = lang_color_tag["style"].split()[-1]
        else:
            lang_color, language = None, None

        stars_built_section = match.div.findNextSibling("div")

        # total stars:
        if stars_built_section.a:
            raw_total_stars = stars_built_section.a.get_text(strip=True)
            if "," in raw_total_stars:
                raw_total_stars = raw_total_stars.replace(",", "")
        if raw_total_stars:
            total_stars: Optional[int]
            try:
                total_stars = int(raw_total_stars)
            except ValueError as missing_number:
                print(missing_number)
        else:
            total_stars = None

        # forks
        if stars_built_section.a.findNextSibling("a"):
            raw_forks = stars_built_section.a.findNextSibling(
                "a",
            ).get_text(strip=True)
            if "," in raw_forks:
                raw_forks = raw_forks.replace(",", "")
        if raw_forks:
            forks: Optional[int]
            try:
                forks = int(raw_forks)
            except ValueError as missing_number:
                print(missing_number)
        else:
            forks = None

        # stars in period
        if stars_built_section.find(
            "span",
            class_="d-inline-block float-sm-right",
        ):
            raw_stars_since = (
                stars_built_section.find(
                    "span",
                    class_="d-inline-block float-sm-right",
                )
                .get_text(strip=True)
                .split()[0]
            )
            if "," in raw_stars_since:
                raw_stars_since = raw_stars_since.replace(",", "")
        if raw_stars_since:
            stars_since: Optional[int]
            try:
                stars_since = int(raw_stars_since)
            except ValueError as missing_number:
                print(missing_number)
        else:
            stars_since = None

        # builtby
        built_section = stars_built_section.find(
            "span",
            class_="d-inline-block mr-3",
        )
        if built_section:
            contributors = stars_built_section.find(
                "span",
                class_="d-inline-block mr-3",
            ).find_all("a")
            built_by = []
            for contributor in contributors:
                contr_data = {}
                contr_data["username"] = contributor["href"].strip("/")
                contr_data["url"] = "https://github.com" + contributor["href"]
                contr_data["avatar"] = contributor.img["src"]
                built_by.append(dict(contr_data))
        repo_instance = Repository(
            rank=rank + 1,
            username=username,
            repository_name=repository_name,
            url=repo_url,
            description=description,
            language=language,
            language_color=lang_color,
            total_stars=total_stars,
            forks=forks,
            stars_since=stars_since,
        )
        trending_repositories.append(repo_instance)
    return trending_repositories


def scraping_developers(
    matches: bs4.element.ResultSet,
) -> List[Developer]:
    """Data about all trending developers are extracted."""
    all_trending_developers = []
    for rank, match in enumerate(matches):

        # relative url of developer
        rel_url = match.div.a["href"]

        # absolute url of developer
        dev_url = "https://github.com" + rel_url

        # username of developer
        username = rel_url.strip("/")

        # developers full name
        name = match.h1.a.get_text(strip=True) if match.h1.a else None

        # avatar url of developer
        avatar = match.img["src"] if match.img else None

        # data about developers popular repo:
        if match.article:
            raw_description = match.article.find(
                "div",
                class_="f6 color-text-secondary mt-1",
            )
            repo_description = (
                raw_description.get_text(
                    strip=True,
                )
                if raw_description
                else None
            )
            pop_repo = match.article.h1.a
            if pop_repo:
                repo_name = pop_repo.get_text(strip=True)
                repo_url = "https://github.com" + pop_repo["href"]
            else:
                repo_name = None
                repo_url = None
        else:
            repo_description = None
            repo_name = None
            repo_url = None

        dev_instance = Developer(
            rank=rank + 1,
            username=username,
            name=name,
            url=dev_url,
            avatar=avatar,
            popular_repo_name=repo_name,
            popular_repo_description=repo_description,
            popular_repo_url=repo_url,
        )
        all_trending_developers.append(dev_instance)
    return all_trending_developers
