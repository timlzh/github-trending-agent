import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import routes
from app.config import Settings
from app.database import create_db_and_tables, get_session
from app.enums import AllowedDateRanges
from app.services.github_trending import get_trending_repos
from app.services.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 创建数据库表
    await create_db_and_tables()

    # 启动调度器
    asyncio.create_task(scheduler.start())

    yield

    # 停止调度器
    scheduler.stop()


app = FastAPI(
    title="GitHub Trending RSS Feed",
    description="AI-powered GitHub trending repositories and developers RSS feed",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="app/templates")

# Register routes
app.include_router(routes.apiRouter, prefix="/api")


@app.get("/")
async def root(
    request: Request,
    since: AllowedDateRanges = AllowedDateRanges.daily,
):
    """
    Root endpoint to fetch trending repositories.
    """
    async with get_session() as session:
        # Fetch trending repositories from the database
        repositories = await get_trending_repos(since=since, session=session)

        return templates.TemplateResponse(
            "index.html",
            {"request": request, "repositories": repositories, "since": since},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=Settings.app.HOST,
        port=Settings.app.PORT,
        log_level=Settings.app.LOG_LEVEL,
    )
