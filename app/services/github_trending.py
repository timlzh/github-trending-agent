from typing import List, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import AllowedDateRanges
from app.models import Repository, TrendingRepository


async def get_trending_repos(
    since: AllowedDateRanges, session: AsyncSession
) -> List[Repository]:
    query = (
        select(TrendingRepository)
        .options(
            selectinload(TrendingRepository.repo).selectinload(Repository.keywords)
        )
        .where(
            TrendingRepository.since == since,
        )
        .order_by(TrendingRepository.rank)  # type: ignore
    )
    result = await session.execute(query)
    trending_repos: Sequence[TrendingRepository] = result.scalars().all()

    return [trending_repo.repo for trending_repo in trending_repos]
