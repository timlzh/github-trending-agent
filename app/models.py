from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.enums import AllowedDateRanges


class Repository(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rank: int
    username: str = Field(index=True)
    repository_name: str = Field(index=True)
    url: str
    description: Optional[str] = None
    language: Optional[str] = None
    language_color: Optional[str] = None
    total_stars: Optional[int] = None
    forks: Optional[int] = None
    stars_since: Optional[int] = None
    ai_summary: Optional[str] = None
    summary_language: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    since: AllowedDateRanges | None = Field(default=None, index=True)

    # Relationships
    trending_repo: Optional["TrendingRepository"] = Relationship(back_populates="repo")
    keywords: list["RepositoryKeyword"] = Relationship(
        back_populates="repository",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class RepositoryKeyword(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    keyword: str
    repository_id: int | None = Field(foreign_key="repository.id")

    # Relationships
    repository: Repository = Relationship(back_populates="keywords")


class TrendingRepository(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    since: AllowedDateRanges
    rank: int
    repo_id: int | None = Field(foreign_key="repository.id")

    # Relationships
    repo: Repository = Relationship(back_populates="trending_repo")


class Developer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rank: int
    username: str
    name: Optional[str] = None
    url: str
    avatar: Optional[str] = None
    popular_repo_name: Optional[str] = None
    popular_repo_description: Optional[str] = None
    popular_repo_url: Optional[str] = None
    ai_summary: Optional[str] = None
    summary_language: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
