"""
SQLAlchemy Models for RatCrawler with Turso Integration
"""

from sqlalchemy import String, Integer, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List, Optional
import json


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class CrawlSession(Base):
    """Model for crawl sessions"""
    __tablename__ = "crawl_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_time: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    seed_urls: Mapped[str] = mapped_column(Text)  # JSON string
    config: Mapped[str] = mapped_column(Text)     # JSON string
    end_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='running')

    # Relationships
    crawled_pages: Mapped[List["CrawledPage"]] = relationship(back_populates="session")
    crawl_errors: Mapped[List["CrawlError"]] = relationship(back_populates="session")

    def __repr__(self) -> str:
        return f"CrawlSession(id={self.id}, status={self.status})"


class CrawledPage(Base):
    """Model for crawled pages"""
    __tablename__ = "crawled_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("crawl_sessions.id"))
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    original_url: Mapped[Optional[str]] = mapped_column(String(2048))
    redirect_chain: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    title: Mapped[Optional[str]] = mapped_column(String(500))
    meta_description: Mapped[Optional[str]] = mapped_column(Text)
    content_text: Mapped[Optional[str]] = mapped_column(Text)
    content_html: Mapped[Optional[str]] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(String(32))
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    page_size: Mapped[Optional[int]] = mapped_column(Integer)
    http_status_code: Mapped[Optional[int]] = mapped_column(Integer)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    language: Mapped[Optional[str]] = mapped_column(String(10))
    charset: Mapped[Optional[str]] = mapped_column(String(50))
    h1_tags: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    h2_tags: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    meta_keywords: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    canonical_url: Mapped[Optional[str]] = mapped_column(String(2048))
    robots_meta: Mapped[Optional[str]] = mapped_column(String(200))
    internal_links_count: Mapped[Optional[int]] = mapped_column(Integer)
    external_links_count: Mapped[Optional[int]] = mapped_column(Integer)
    images_count: Mapped[Optional[int]] = mapped_column(Integer)
    content_type: Mapped[Optional[str]] = mapped_column(String(50))  # Content type: html, pdf, image, document, etc.
    file_extension: Mapped[Optional[str]] = mapped_column(String(10))  # File extension: .pdf, .jpg, .doc, etc.
    crawl_time: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    session: Mapped["CrawlSession"] = relationship(back_populates="crawled_pages")

    def __repr__(self) -> str:
        return f"CrawledPage(id={self.id}, url={self.url[:50]}...)"


class CrawlError(Base):
    """Model for crawl errors"""
    __tablename__ = "crawl_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("crawl_sessions.id"))
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    error_type: Mapped[str] = mapped_column(String(100))
    error_msg: Mapped[str] = mapped_column(Text)
    status_code: Mapped[Optional[int]] = mapped_column(Integer)
    timestamp: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    session: Mapped["CrawlSession"] = relationship(back_populates="crawl_errors")

    def __repr__(self) -> str:
        return f"CrawlError(id={self.id}, url={self.url[:50]}..., type={self.error_type})"


class WebData(Base):
    """Model for web data collection (legacy table)"""
    __tablename__ = "webdata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    content: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    crawled_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"WebData(id={self.id}, url={self.url[:50]}...)"


class DomainAuthority(Base):
    """Model for domain authority tracking"""
    __tablename__ = "domain_authority"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    authority_score: Mapped[float] = mapped_column(Float, default=0.0)
    backlinks_count: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"DomainAuthority(domain={self.domain}, score={self.authority_score})"


class Backlink(Base):
    """Model for backlinks data"""
    __tablename__ = "backlinks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    anchor_text: Mapped[Optional[str]] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text)
    page_title: Mapped[Optional[str]] = mapped_column(String(500))
    domain_authority: Mapped[float] = mapped_column(Float, default=0.0)
    is_nofollow: Mapped[bool] = mapped_column(Boolean, default=False)
    crawl_date: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"Backlink(id={self.id}, source={self.source_url[:30]}..., target={self.target_url[:30]}...)"


class PageRankScore(Base):
    """Model for PageRank scores"""
    __tablename__ = "pagerank_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    pagerank_score: Mapped[float] = mapped_column(Float, default=0.0)
    last_calculated: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"PageRankScore(url={self.url[:50]}..., score={self.pagerank_score})"


class DomainScore(Base):
    """Model for domain scores"""
    __tablename__ = "domain_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    authority_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_backlinks: Mapped[int] = mapped_column(Integer, default=0)
    unique_referring_domains: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"DomainScore(domain={self.domain}, score={self.authority_score})"
