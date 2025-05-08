import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
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
        repositories = await self.github_service.get_trending_repositories(
            since=since,
        )

        for repo in repositories:
            try:
                result = await session.execute(
                    select(Repository).where(
                        Repository.repository_name == repo.repository_name,
                        Repository.username == repo.username,
                        Repository.summary_language == Settings.ai.SUMMARY_LANGUAGE,
                        Repository.since == since,
                    )
                )
                existing_repo: Repository | None = result.scalar_one_or_none()

                current_time = datetime.now(UTC)
                if not existing_repo or existing_repo.created_at.replace(
                    tzinfo=UTC
                ) < current_time - timedelta(
                    hours=Settings.app.SCHEDULER_INTERVAL_HOURS
                ):
                    logging.info(
                        f"Updating repository {repo.username}/{repo.repository_name}"
                    )
                    ai_summary = await self.ai_service.generate_summary(repo)
                    logging.info(f"AI summary: {ai_summary}")
                    repo.ai_summary = ai_summary
                    repo.summary_language = Settings.ai.SUMMARY_LANGUAGE
                    repo.since = since

                    if existing_repo:
                        await session.delete(existing_repo)
                    session.add(repo)
                    await session.commit()
                    await session.refresh(repo)

                    ai_keywords = await self.ai_service.generate_tags(repo)
                    logging.info(f"AI keywords: {ai_keywords}")
                    keywords = [
                        RepositoryKeyword(keyword=keyword, repository_id=repo.id)
                        for keyword in ai_keywords
                    ]
                    session.add_all(keywords)
                    await session.commit()
                    await session.refresh(repo)
                else:
                    repo = existing_repo
                    logging.info(
                        f"Repository {repo.username}/{repo.repository_name} already exists"
                    )

                # 更新趋势仓库
                result = await session.execute(
                    select(TrendingRepository).where(
                        TrendingRepository.since == since,
                        TrendingRepository.rank == repo.rank,
                    )
                )
                trending_repo: TrendingRepository | None = result.scalar_one_or_none()
                if trending_repo:
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
                await session.refresh(trending_repo)
            except Exception as e:
                logging.error(
                    f"Error processing repository {repo.username}/{repo.repository_name}: {e}"
                )
                await session.rollback()
                continue

    # async def _update_developers(
    #     self,
    #     session: Session,
    #     since: AllowedDateRanges,
    # ):
    #     developers = await self.github_service.get_trending_developers(
    #         since=since,
    #     )

    #     for dev in developers:
    #         existing_dev = session.exec(
    #             select(Developer).where(
    #                 Developer.username == dev.username,
    #             )
    #         ).first()

    #         current_time = datetime.now(UTC)
    #         if not existing_dev or existing_dev.created_at.replace(
    #             tzinfo=UTC
    #         ) < current_time - timedelta(hours=Settings.app.SCHEDULER_INTERVAL_HOURS):
    #             ai_summary = await self.ai_service.generate_summary(dev)
    #             dev.ai_summary = ai_summary
    #             dev.summary_language = Settings.ai.SUMMARY_LANGUAGE

    #             session.add(dev)
    #             if existing_dev:
    #                 session.delete(existing_dev)
    #             session.commit()
    #             session.refresh(dev)

    async def start(self):
        """启动调度器"""
        self.is_running = True
        while self.is_running:
            try:
                await self.update_trending_data()
                # 等待指定的时间间隔
                await asyncio.sleep(Settings.app.SCHEDULER_INTERVAL_HOURS * 3600)
            except Exception as e:
                print(f"Error in scheduler: {e}")
                await asyncio.sleep(60)  # 发生错误时等待1分钟后重试

    def stop(self):
        """停止调度器"""
        self.is_running = False


# 创建全局调度器实例
scheduler = TrendingScheduler()
