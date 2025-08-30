"""
SQLAlchemy Database Handler for RatCrawler with Turso Integration
"""

import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select, insert, update, delete, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from rat.models import (
    Base, CrawlSession, CrawledPage, CrawlError, WebData,
    DomainAuthority, Backlink, PageRankScore, DomainScore
)
from rat.config import config


class SQLAlchemyDatabase:
    """
    SQLAlchemy-based database handler with Turso support
    """

    def __init__(self, db_url: Optional[str] = None, echo: bool = False):
        """Initialize SQLAlchemy database connection"""
        self.db_url = db_url or self._get_database_url()

        # Set up connect_args for Turso authentication
        connect_args = {}
        if config.TURSO_DATABASE_URL and config.TURSO_AUTH_TOKEN:
            connect_args = {
                "auth_token": config.TURSO_AUTH_TOKEN,
            }

        self.engine = create_engine(self.db_url, echo=echo, connect_args=connect_args)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        self._create_tables()

    def _get_database_url(self) -> str:
        """Get database URL from config or environment"""
        if config.TURSO_DATABASE_URL and config.TURSO_AUTH_TOKEN:
            # Use Turso with SQLite dialect and connect_args
            return f"sqlite+{config.TURSO_DATABASE_URL}?secure=true"
        else:
            # Fallback to local SQLite
            db_path = config.LOCAL_DB_PATH
            return f"sqlite:///{db_path}"

    def _create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("✅ Database tables created successfully")
        except SQLAlchemyError as e:
            print(f"❌ Error creating tables: {e}")
            raise

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def close_session(self, session: Session):
        """Close database session"""
        session.close()

    # Crawl Session Methods
    def create_crawl_session(self, seed_urls: List[str], config_data: Dict) -> str:
        """Create new crawl session"""
        with self.get_session() as session:
            try:
                crawl_session = CrawlSession(
                    seed_urls=str(seed_urls),  # Convert to string for storage
                    config=str(config_data)
                )
                session.add(crawl_session)
                session.commit()
                session.refresh(crawl_session)
                return str(crawl_session.id)
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error creating crawl session: {e}")
                raise

    def finish_crawl_session(self, session_id: str, status: str):
        """Finish crawl session"""
        with self.get_session() as session:
            try:
                stmt = (
                    update(CrawlSession)
                    .where(CrawlSession.id == int(session_id))
                    .values(end_time=datetime.now(), status=status)
                )
                session.execute(stmt)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error finishing crawl session: {e}")

    def get_crawl_summary(self, session_id: str) -> Dict:
        """Get crawl session summary"""
        with self.get_session() as session:
            try:
                # Get session info
                session_stmt = select(CrawlSession).where(CrawlSession.id == int(session_id))
                crawl_session = session.execute(session_stmt).scalar_one_or_none()

                if not crawl_session:
                    return {}

                # Get page statistics
                pages_stmt = select(
                    func.count(CrawledPage.id).label('total_pages'),
                    func.avg(CrawledPage.word_count).label('avg_word_count'),
                    func.sum(CrawledPage.page_size).label('total_size'),
                    func.avg(CrawledPage.response_time_ms).label('avg_response_time')
                ).where(CrawledPage.session_id == int(session_id))

                result = session.execute(pages_stmt).first()

                if result:
                    return {
                        'total_pages': result.total_pages or 0,
                        'avg_word_count': float(result.avg_word_count) if result.avg_word_count else 0,
                        'total_size': result.total_size or 0,
                        'avg_response_time': float(result.avg_response_time) if result.avg_response_time else 0
                    }
                else:
                    return {
                        'total_pages': 0,
                        'avg_word_count': 0,
                        'total_size': 0,
                        'avg_response_time': 0
                    }
            except SQLAlchemyError as e:
                print(f"❌ Error getting crawl summary: {e}")
                return {}

    # Crawled Pages Methods
    def store_crawled_page(self, page_data: Dict, session_id: str):
        """Store crawled page data"""
        with self.get_session() as session:
            try:
                crawled_page = CrawledPage(
                    session_id=int(session_id),
                    url=page_data.get('url', ''),
                    original_url=page_data.get('original_url'),
                    redirect_chain=str(page_data.get('redirect_chain', [])),
                    title=page_data.get('title'),
                    meta_description=page_data.get('meta_description'),
                    content_text=page_data.get('content_text'),
                    content_html=page_data.get('content_html'),
                    content_hash=page_data.get('content_hash'),
                    word_count=page_data.get('word_count'),
                    page_size=page_data.get('page_size'),
                    http_status_code=page_data.get('http_status_code'),
                    response_time_ms=page_data.get('response_time_ms'),
                    language=page_data.get('language'),
                    charset=page_data.get('charset'),
                    h1_tags=str(page_data.get('h1_tags', [])),
                    h2_tags=str(page_data.get('h2_tags', [])),
                    meta_keywords=str(page_data.get('meta_keywords', [])),
                    canonical_url=page_data.get('canonical_url'),
                    robots_meta=page_data.get('robots_meta'),
                    internal_links_count=page_data.get('internal_links_count'),
                    external_links_count=page_data.get('external_links_count'),
                    images_count=page_data.get('images_count')
                )
                session.add(crawled_page)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error storing crawled page: {e}")

    def get_all_crawled_urls(self) -> List[str]:
        """Get all crawled URLs"""
        with self.get_session() as session:
            try:
                stmt = select(CrawledPage.url)
                result = session.execute(stmt).scalars().all()
                return list(result)
            except SQLAlchemyError as e:
                print(f"❌ Error getting crawled URLs: {e}")
                return []

    def get_all_content_hashes(self) -> List[str]:
        """Get all content hashes"""
        with self.get_session() as session:
            try:
                stmt = select(CrawledPage.content_hash).where(CrawledPage.content_hash.isnot(None))
                result = session.execute(stmt).scalars().all()
                return [h for h in result if h is not None]
            except SQLAlchemyError as e:
                print(f"❌ Error getting content hashes: {e}")
                return []

    def get_last_crawl_time(self, url: str) -> Optional[str]:
        """Get last crawl time for URL"""
        with self.get_session() as session:
            try:
                stmt = select(CrawledPage.crawl_time).where(CrawledPage.url == url).order_by(CrawledPage.crawl_time.desc()).limit(1)
                result = session.execute(stmt).scalar_one_or_none()
                return str(result) if result else None
            except SQLAlchemyError as e:
                print(f"❌ Error getting last crawl time: {e}")
                return None

    # Error Logging Methods
    def log_crawl_error(self, session_id: str, url: str, error_type: str, error_msg: str, status_code: Optional[int] = None):
        """Log crawl error"""
        with self.get_session() as session:
            try:
                crawl_error = CrawlError(
                    session_id=int(session_id),
                    url=url,
                    error_type=error_type,
                    error_msg=error_msg,
                    status_code=status_code
                )
                session.add(crawl_error)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error logging crawl error: {e}")

    # Backlinks Methods
    def store_backlinks(self, backlinks: List[Any], session_id: Optional[str] = None):
        """Store backlinks in database (compatible with backlinkprocessor interface)"""
        with self.get_session() as session:
            try:
                for backlink in backlinks:
                    if hasattr(backlink, 'source_url'):
                        db_backlink = Backlink(
                            source_url=backlink.source_url,
                            target_url=backlink.target_url,
                            anchor_text=getattr(backlink, 'anchor_text', ''),
                            context=getattr(backlink, 'context', ''),
                            page_title=getattr(backlink, 'page_title', ''),
                            domain_authority=getattr(backlink, 'domain_authority', 0.0),
                            is_nofollow=getattr(backlink, 'is_nofollow', False)
                        )
                        session.add(db_backlink)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error storing backlinks: {e}")

    def store_domain_scores(self, domain_scores: Dict[str, float]):
        """Store domain authority scores (alias for store_domain_stats)"""
        self.store_domain_stats(domain_scores)

    def get_all_backlinks(self) -> List[Dict]:
        """Get all backlinks"""
        with self.get_session() as session:
            try:
                stmt = select(Backlink)
                result = session.execute(stmt).scalars().all()

                backlinks = []
                for bl in result:
                    backlinks.append({
                        'source_url': bl.source_url,
                        'target_url': bl.target_url,
                        'anchor_text': bl.anchor_text,
                        'context': bl.context,
                        'page_title': bl.page_title,
                        'domain_authority': bl.domain_authority,
                        'is_nofollow': bl.is_nofollow,
                        'crawl_date': str(bl.crawl_date) if bl.crawl_date else None
                    })
                return backlinks
            except SQLAlchemyError as e:
                print(f"❌ Error getting backlinks: {e}")
                return []

    # Domain Authority Methods
    def get_domain_authority_scores(self) -> Dict[str, float]:
        """Get domain authority scores"""
        with self.get_session() as session:
            try:
                stmt = select(DomainAuthority.domain, DomainAuthority.authority_score)
                result = session.execute(stmt).all()
                return {row.domain: row.authority_score for row in result}
            except SQLAlchemyError as e:
                print(f"❌ Error getting domain authority scores: {e}")
                return {}

    def store_domain_stats(self, domain_scores: Dict[str, float]):
        """Store domain authority scores"""
        with self.get_session() as session:
            try:
                for domain, score in domain_scores.items():
                    # Upsert domain authority
                    stmt = select(DomainAuthority).where(DomainAuthority.domain == domain)
                    existing = session.execute(stmt).scalar_one_or_none()

                    if existing:
                        stmt = (
                            update(DomainAuthority)
                            .where(DomainAuthority.domain == domain)
                            .values(authority_score=score, last_updated=datetime.now())
                        )
                        session.execute(stmt)
                    else:
                        domain_auth = DomainAuthority(domain=domain, authority_score=score)
                        session.add(domain_auth)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error storing domain stats: {e}")

    # PageRank Methods
    def store_pagerank_scores(self, pagerank_scores: Dict[str, float]):
        """Store PageRank scores"""
        with self.get_session() as session:
            try:
                for url, score in pagerank_scores.items():
                    # Upsert PageRank score
                    stmt = select(PageRankScore).where(PageRankScore.url == url)
                    existing = session.execute(stmt).scalar_one_or_none()

                    if existing:
                        stmt = (
                            update(PageRankScore)
                            .where(PageRankScore.url == url)
                            .values(pagerank_score=score, last_calculated=datetime.now())
                        )
                        session.execute(stmt)
                    else:
                        pr_score = PageRankScore(url=url, pagerank_score=score)
                        session.add(pr_score)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error storing PageRank scores: {e}")

    def get_pagerank_scores(self) -> Dict[str, float]:
        """Get PageRank scores"""
        with self.get_session() as session:
            try:
                stmt = select(PageRankScore.url, PageRankScore.pagerank_score)
                result = session.execute(stmt).all()
                return {row.url: row.pagerank_score for row in result}
            except SQLAlchemyError as e:
                print(f"❌ Error getting PageRank scores: {e}")
                return {}

    # WebData Methods (Legacy)
    def insert_webdata(self, document: Dict) -> str:
        """Insert webdata document (legacy compatibility)"""
        with self.get_session() as session:
            try:
                import json
                webdata = WebData(
                    url=document.get('url', ''),
                    title=document.get('title'),
                    content=document.get('content'),
                    metadata_json=json.dumps({k: v for k, v in document.items()
                                       if k not in ['url', 'title', 'content']})
                )
                session.add(webdata)
                session.commit()
                session.refresh(webdata)
                return str(webdata.id)
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error inserting webdata: {e}")
                return ""

    def find_webdata(self, query: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """Find webdata documents"""
        with self.get_session() as session:
            try:
                stmt = select(WebData)
                if query:
                    conditions = []
                    for key, value in query.items():
                        if key == 'url':
                            conditions.append(WebData.url == value)
                        elif key == 'title':
                            conditions.append(WebData.title == value)
                    if conditions:
                        stmt = stmt.where(and_(*conditions))

                stmt = stmt.limit(limit)
                result = session.execute(stmt).scalars().all()

                documents = []
                for wd in result:
                    doc = {
                        'id': wd.id,
                        'url': wd.url,
                        'title': wd.title,
                        'content': wd.content,
                        'crawled_at': str(wd.crawled_at) if wd.crawled_at else None,
                        'updated_at': str(wd.updated_at) if wd.updated_at else None
                    }
                    if wd.metadata_json:
                        import json
                        try:
                            doc.update(json.loads(wd.metadata_json))
                        except:
                            pass
                    documents.append(doc)
                return documents
            except SQLAlchemyError as e:
                print(f"❌ Error finding webdata: {e}")
                return []

    # Utility Methods
    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Clean up old data"""
        with self.get_session() as session:
            try:
                cutoff_date = datetime.now() - timedelta(days=days_old)

                # Delete old crawl sessions
                stmt = delete(CrawlSession).where(CrawlSession.start_time < cutoff_date)
                result = session.execute(stmt)

                deleted_count = result.rowcount
                session.commit()
                return deleted_count
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error cleaning up old data: {e}")
                return 0

    def get_recent_backlinks(self, hours: int = 24) -> List[Dict]:
        """Get recent backlinks"""
        with self.get_session() as session:
            try:
                from datetime import timedelta
                cutoff_time = datetime.now() - timedelta(hours=hours)

                stmt = select(Backlink).where(Backlink.crawl_date >= cutoff_time)
                result = session.execute(stmt).scalars().all()

                backlinks = []
                for bl in result:
                    backlinks.append({
                        'source_url': bl.source_url,
                        'target_url': bl.target_url,
                        'anchor_text': bl.anchor_text,
                        'crawl_date': str(bl.crawl_date) if bl.crawl_date else None
                    })
                return backlinks
            except SQLAlchemyError as e:
                print(f"❌ Error getting recent backlinks: {e}")
                return []

    def get_discovered_subdomains(self) -> List[str]:
        """Get discovered subdomains from crawled URLs"""
        with self.get_session() as session:
            try:
                from urllib.parse import urlparse
                stmt = select(CrawledPage.url)
                result = session.execute(stmt).scalars().all()

                subdomains = set()
                for url in result:
                    parsed = urlparse(url)
                    if parsed.netloc:
                        # Extract subdomain from netloc
                        parts = parsed.netloc.split('.')
                        if len(parts) > 2:
                            subdomain = '.'.join(parts[:-2])  # Everything except the main domain
                            if subdomain:
                                subdomains.add(f"https://{parsed.netloc}")

                return list(subdomains)
            except SQLAlchemyError as e:
                print(f"❌ Error getting discovered subdomains: {e}")
                return []

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            print("✅ Database connection closed")


# Global database instance
_db_instance = None


def get_database() -> SQLAlchemyDatabase:
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SQLAlchemyDatabase()
    return _db_instance


# Backward compatibility
Database = SQLAlchemyDatabase
