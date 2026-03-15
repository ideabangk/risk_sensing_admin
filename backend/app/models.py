from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    NEWS = "NEWS"
    BLOG = "BLOG"
    CAFE = "CAFE"
    CONSUMER_AGENCY = "CONSUMER_AGENCY"
    DART = "DART"


class Sentiment(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MIDDLE = "MIDDLE"
    LOW = "LOW"
    NONE = "NONE"


class CompanyBase(BaseModel):
    name: str
    search_keywords: Optional[List[str]] = None
    is_active: bool = True


class CompanyCreate(CompanyBase):
    pass


class Company(CompanyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ArticleBase(BaseModel):
    company_id: int
    source_type: SourceType
    title: str
    content: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    sentiment: Sentiment = Sentiment.NEUTRAL
    risk_level: RiskLevel = RiskLevel.LOW
    risk_keywords: List[str] = []
    summary: Optional[str] = None


class ArticleCreate(ArticleBase):
    pass


class Article(ArticleBase):
    id: int
    collected_at: datetime

    class Config:
        from_attributes = True


class ArticleFilter(BaseModel):
    company_id: Optional[int] = None
    source_type: Optional[SourceType] = None
    sentiment: Optional[Sentiment] = None
    risk_level: Optional[RiskLevel] = None
    keyword: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    size: int = 20


class BatchLogCreate(BaseModel):
    company_id: Optional[int] = None
    source_type: Optional[str] = None


class BatchLog(BatchLogCreate):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    articles_collected: int
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_articles: int
    articles_today: int
    critical_count: int
    high_count: int
    middle_count: int
    low_count: int
    negative_ratio: float
    top_risk_companies: List[dict]
    recent_critical: List[dict]
    source_distribution: List[dict]
    daily_trend: List[dict]
