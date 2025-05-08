from typing import List

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import get_session
from app.enums import AllowedDateRanges
from app.models import Repository
from app.services.github_trending import get_trending_repos
from app.services.rss import RSSService

apiRouter = APIRouter()
rss_service = RSSService(Settings.app.BASE_URL)


@apiRouter.get("/trending/repositories/{since}")
async def get_trending_repositories(
    since: AllowedDateRanges = AllowedDateRanges.daily,
):
    async with get_session() as session:
        repositories: List[Repository] = await get_trending_repos(
            since=since,
            session=session,
        )
        rss_content = rss_service.generate_repository_feed(repositories, since)
        return Response(content=rss_content, media_type="application/xml")


# @router.get("/trending/developers/{since}")
# async def get_trending_developers(
#     since: AllowedDateRanges = AllowedDateRanges.daily,
#     session: Session = Depends(get_session),
# ):
#     # 从数据库中获取最新的开发者数据
#     query = select(Developer)
#     developers: List[Developer] = list(session.exec(query).all())

#     # 按排名排序
#     developers.sort(key=lambda x: x.rank)

#     # 生成 RSS feed
#     rss_content = rss_service.generate_developer_feed(developers, since.value)
#     return Response(content=rss_content, media_type="application/xml")
