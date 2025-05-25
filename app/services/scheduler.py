import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.config import Settings
from app.database import get_session
from app.enums import AllowedDateRanges
from app.models import Repository, RepositoryKeyword, TrendingRepository
from app.services.ai import AISummaryService
from app.services.github import GitHubTrendingService


class TrendingScheduler:
    def __init__(self):
        self.github_service = GitHubTrendingService()
        self.ai_service = AISummaryService()
        self.is_running = False
        self.is_any_failure = False

    async def update_trending_data(self):
        """更新所有趋势数据"""
        async with get_session() as session:
            # 更新所有时间范围的仓库数据
            for since in AllowedDateRanges:
                await self._update_repositories(session, since)
            # # 更新所有时间范围的开发者数据
            # for since in AllowedDateRanges:
            #     await self._update_developers(session, since)

    async def _update_repositories(
        self,
        session: AsyncSession,
        since: AllowedDateRanges,
    ):
        self.is_any_failure = False
        repositories = await self.github_service.get_trending_repositories(
            since=since,
        )

        for repo in repositories:
            try:
                result = await session.execute(
                    select(Repository)
                    .options(selectinload(Repository.keywords))
                    .where(
                        Repository.repository_name == repo.repository_name,
                        Repository.username == repo.username,
                        Repository.summary_language == Settings.ai.SUMMARY_LANGUAGE,
                        Repository.since == since,
                    )
                )
                existing_repo: Repository | None = result.scalar_one_or_none()

                current_time = datetime.now(UTC)
                update_time_threshold = current_time - timedelta(
                    hours=Settings.app.UPDATE_INTERVAL
                )
                if (
                    not existing_repo
                    or existing_repo.created_at.replace(tzinfo=UTC)
                    < update_time_threshold
                    or existing_repo.ai_summary is None
                    or len(existing_repo.keywords) == 0
                ):
                    logging.info(
                        f"Updating repository {repo.username}/{repo.repository_name}"
                    )
                    try:
                        ai_summary = await self.ai_service.generate_summary(repo)
                    except Exception as e:
                        logging.error(
                            f"Error generating AI summary for {repo.username}/{repo.repository_name}: {e}"
                        )
                        ai_summary = None
                        self.is_any_failure = True
                    logging.info(f"AI summary: {ai_summary}")
                    repo.ai_summary = ai_summary
                    repo.summary_language = Settings.ai.SUMMARY_LANGUAGE
                    repo.since = since

                    if existing_repo:
                        await session.delete(existing_repo)
                    session.add(repo)
                    await session.commit()

                    try:
                        ai_keywords = await self.ai_service.generate_tags(repo)
                        logging.info(f"AI keywords: {ai_keywords}")
                        keywords = [
                            RepositoryKeyword(keyword=keyword, repository_id=repo.id)
                            for keyword in ai_keywords
                        ]
                        if len(keywords) > 3:
                            keywords = keywords[:3]
                        session.add_all(keywords)
                        await session.commit()
                    except Exception as e:
                        logging.error(
                            f"Error generating AI keywords for {repo.username}/{repo.repository_name}: {e}"
                        )
                        self.is_any_failure = True
                else:
                    repo = existing_repo
                    logging.info(
                        f"Repository {repo.username}/{repo.repository_name} already exists"
                    )

                # 更新趋势仓库
                result = await session.execute(
                    select(TrendingRepository)
                    .options(
                        selectinload(TrendingRepository.repo).selectinload(
                            Repository.keywords
                        )
                    )
                    .where(
                        TrendingRepository.since == since,
                        TrendingRepository.rank == repo.rank,
                    )
                )
                trending_repo: TrendingRepository | None = result.scalar_one_or_none()
                if trending_repo:
                    trending_repo.repo_id = repo.id
                    trending_repo.repo = repo
                else:
                    trending_repo = TrendingRepository(
                        since=since,
                        rank=repo.rank,
                        repo_id=repo.id,
                        repo=repo,
                    )
                session.add(trending_repo)
                await session.commit()

                # last check
                if any(
                    [
                        trending_repo.repo_id is None,
                        trending_repo.repo is None,
                        trending_repo.repo.ai_summary is None,
                        len(trending_repo.repo.keywords) == 0,
                    ]
                ):
                    logging.error(
                        f"Error: {repo.username}/{repo.repository_name} is missing data after processing"
                    )
                    self.is_any_failure = True
            except Exception as e:
                logging.error(
                    f"Error processing repository {repo.username}/{repo.repository_name}: {e}"
                )
                self.is_any_failure = True
                continue

    async def start(self):
        """启动调度器"""
        self.is_running = True
        while self.is_running:
            try:
                await self.update_trending_data()
                if self.is_any_failure:
                    await asyncio.sleep(60)  # 如果发生错误，等待1分钟后重试
                else:
                    await asyncio.sleep(
                        Settings.app.UPDATE_INTERVAL * 60
                    )  # 等待指定的时间间隔
            except Exception as e:
                print(f"Error in scheduler: {e}")
                await asyncio.sleep(60)  # 发生错误时等待1分钟后重试

    def stop(self):
        """停止调度器"""
        self.is_running = False


# 创建全局调度器实例
scheduler = TrendingScheduler()
