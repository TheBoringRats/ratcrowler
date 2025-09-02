"""
SQLAlchemy Database Handler for RatCrawler with Turso Integration
Enhanced with improved database selection and management
"""

import os
import itertools
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select, update, delete, and_, func, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import time

from .models import (
    Base, CrawlSession, CrawledPage, CrawlError, WebData,
    DomainAuthority, Backlink, PageRankScore, DomainScore
)
from .config import config
from .healthcheck import Health
from .dblist import DBList
from .logger import log_db_operation, get_logger


class SQLAlchemyDatabase:
    """
    SQLAlchemy-based database handler with Turso support
    Includes load balancing + quota checks (5GB, 10M writes/day).
    Enhanced with improved database selection and management.
    """

    STORAGE_LIMIT_BYTES = 5 * 1024 * 1024 * 1024  # 5GB
    DAILY_WRITE_LIMIT = 10_000_000  # 10 million

    def __init__(self, echo: bool = False):
        self.health = Health()
        self.db_list = DBList()
        self.echo = echo

        # Initialize health check to populate useable databases
        self.health.useabledbdata()

        # Pre-validated DBs from Health (already passed 5GB/10M rules)
        self.crwlDB = self.health.useable_databases_crawler
        self.bcklDB = self.health.useable_databases_backlink

        self.databaselist1 = []  # crawl DBs
        self.databaselist2 = []  # backlink DBs

        self.__enginelist()

        # Round robin cycles
        self._cycle_crawl = itertools.cycle(self.databaselist1) if self.databaselist1 else None
        self._cycle_backlink = itertools.cycle(self.databaselist2) if self.databaselist2 else None

        # Create tables in all databases
        self._create_tables()

        # Migrate tables to add missing columns
        self._migrate_tables()

    def __enginelist(self):
        """Build engines + sessionmakers for all DBs with optimized settings"""
        for db in self.crwlDB:
            if db:
                engine = create_engine(
                    f"sqlite+{db['url']}?secure=true",
                    connect_args={
                        "auth_token": db['auth_token'],
                        "check_same_thread": False
                    },
                    pool_pre_ping=True,  # Verify connections before use
                    pool_recycle=3600,   # Recycle connections every hour
                    echo=self.echo
                )
                db['engine'] = engine
                db['sessionmaker'] = sessionmaker(
                    bind=engine,
                    autocommit=False,
                    autoflush=False,
                    expire_on_commit=False  # Prevent lazy loading issues
                )
                self.databaselist1.append(db)

        for dbx in self.bcklDB:
            if dbx:
                engine = create_engine(
                    f"sqlite+{dbx['url']}?secure=true",
                    connect_args={
                        "check_same_thread": False,
                        "auth_token": dbx['auth_token']
                    },
                    pool_pre_ping=True,  # Verify connections before use
                    pool_recycle=3600,   # Recycle connections every hour
                    echo=self.echo
                )
                dbx['engine'] = engine
                dbx['sessionmaker'] = sessionmaker(
                    bind=engine,
                    autocommit=False,
                    autoflush=False,
                    expire_on_commit=False  # Prevent lazy loading issues
                )
                self.databaselist2.append(dbx)

    def _check_quota(self, db: Dict) -> bool:
        """
        Check if DB is under quota using health.current_limit().
        Returns True if usable.
        """
        usage = self.health.current_limit(db['name'], db['organization'], db['apikey'])
        if not usage:
            return False

        storage = usage.get("storage_bytes", 0)
        writes = usage.get("rows_written", 0)

        # Ensure values are not None
        if storage is None:
            storage = 0
        if writes is None:
            writes = 0

        return storage < self.STORAGE_LIMIT_BYTES and writes < self.DAILY_WRITE_LIMIT

    def _choose_db(self, db_type: str) -> Optional[Dict]:
        """
        Pick next DB (round-robin), skip if over quota.
        Enhanced with better error handling and validation.
        """
        if db_type == "crawl":
            if not self.databaselist1:
                raise RuntimeError("No crawl databases available")
            cycle = self._cycle_crawl
            db_list = self.databaselist1
        elif db_type == "backlink":
            if not self.databaselist2:
                raise RuntimeError("No backlink databases available")
            cycle = self._cycle_backlink
            db_list = self.databaselist2
        else:
            raise ValueError(f"Invalid db_type: {db_type}. Must be 'crawl' or 'backlink'")

        if not cycle:
            raise RuntimeError(f"No {db_type} database cycle available")

        checked = set()
        max_attempts = len(db_list)  # Don't check more than available DBs

        for _ in range(max_attempts):
            db = next(cycle)
            if db['name'] in checked:
                continue  # Skip already checked DB

            checked.add(db['name'])

            if self._check_quota(db):

                return db

        # All databases are over quota
        return None

    def get_session(self, db_type: str = "crawl") -> Session:
        """
        Get a SQLAlchemy session for selected DB (with quota check)
        Enhanced with better error messages and validation.
        """
        if db_type not in ["crawl", "backlink"]:
            raise ValueError(f"Invalid db_type: {db_type}. Must be 'crawl' or 'backlink'")

        db = self._choose_db(db_type)
        if not db:
            # Provide more specific error information
            db_count = len(self.databaselist1) if db_type == "crawl" else len(self.databaselist2)
            raise RuntimeError(
                f"No available {db_type} database under quota. "
                f"Total {db_type} databases: {db_count}. "
                f"All databases may be over storage (5GB) or daily write (10M) limits."
            )

        try:
            session = db['sessionmaker']()
            return session
        except Exception as e:
            raise RuntimeError(f"Failed to create session for {db_type} database {db['name']}: {e}")

    def get_specific_db_session(self, db_name: str, db_type: str = "crawl") -> Session:
        """
        Get a session for a specific database by name.
        Useful when you need to access a specific DB (like in store_crawled_page).
        """
        if db_type == "crawl":
            db_list = self.databaselist1
        elif db_type == "backlink":
            db_list = self.databaselist2
        else:
            raise ValueError(f"Invalid db_type: {db_type}. Must be 'crawl' or 'backlink'")

        # Find the specific database
        db = next((d for d in db_list if d['name'] == db_name), None)
        if not db:
            available_dbs = [d['name'] for d in db_list]
            raise RuntimeError(
                f"Database '{db_name}' not found in {db_type} databases. "
                f"Available {db_type} databases: {available_dbs}"
            )

        # Check quota before returning session
        if not self._check_quota(db):
            raise RuntimeError(f"Database '{db_name}' is over quota limits")

        try:
            return db['sessionmaker']()
        except Exception as e:
            raise RuntimeError(f"Failed to create session for database {db_name}: {e}")

    def get_available_databases(self, db_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get list of available database names by type.
        Useful for debugging and monitoring.
        """
        result = {}

        if db_type is None or db_type == "crawl":
            result["crawl"] = [db['name'] for db in self.databaselist1]

        if db_type is None or db_type == "backlink":
            result["backlink"] = [db['name'] for db in self.databaselist2]

        return result

    def get_database_health_status(self) -> Dict:
        """
        Get health status of all databases including quota usage.
        """
        status = {
            "crawl_databases": [],
            "backlink_databases": [],
            "total_available": {
                "crawl": 0,
                "backlink": 0
            }
        }

        # Check crawl databases
        for db in self.databaselist1:
            usage = self.health.current_limit(db['name'], db['organization'], db['apikey'])
            is_available = self._check_quota(db) if usage else False

            status["crawl_databases"].append({
                "name": db['name'],
                "available": is_available,
                "storage_bytes": usage.get("storage_bytes", 0) if usage else 0,
                "storage_gb": round((usage.get("storage_bytes", 0) / (1024**3)), 2) if usage else 0,
                "rows_written": usage.get("rows_written", 0) if usage else 0,
                "storage_limit_reached": (usage.get("storage_bytes", 0) >= self.STORAGE_LIMIT_BYTES) if usage else False,
                "write_limit_reached": (usage.get("rows_written", 0) >= self.DAILY_WRITE_LIMIT) if usage else False
            })

            if is_available:
                status["total_available"]["crawl"] += 1

        # Check backlink databases
        for db in self.databaselist2:
            usage = self.health.current_limit(db['name'], db['organization'], db['apikey'])
            is_available = self._check_quota(db) if usage else False

            status["backlink_databases"].append({
                "name": db['name'],
                "available": is_available,
                "storage_bytes": usage.get("storage_bytes", 0) if usage else 0,
                "storage_gb": round((usage.get("storage_bytes", 0) / (1024**3)), 2) if usage else 0,
                "rows_written": usage.get("rows_written", 0) if usage else 0,
                "storage_limit_reached": (usage.get("storage_bytes", 0) >= self.STORAGE_LIMIT_BYTES) if usage else False,
                "write_limit_reached": (usage.get("rows_written", 0) >= self.DAILY_WRITE_LIMIT) if usage else False
            })

            if is_available:
                status["total_available"]["backlink"] += 1

        return status

    def _create_tables(self):
        """Create tables in all databases"""
        try:
            for db in (self.databaselist1 + self.databaselist2):
                engine = db.get('engine')
                if engine:
                    Base.metadata.create_all(engine)
                    print(f"✅ Tables created successfully in database: {db.get('name')}")
        except SQLAlchemyError as e:
            print(f"❌ Error creating tables: {e}")
            raise

    def _migrate_tables(self):
        """Migrate existing tables to add missing columns"""
        migration_sql = [
            "ALTER TABLE crawled_pages ADD COLUMN content_type TEXT;",  # Add if missing
            "ALTER TABLE crawled_pages ADD COLUMN file_extension TEXT;",  # Add if missing
            # Add more ALTER statements here if other columns are missing (e.g., from future model updates)
        ]

        for db in (self.databaselist1 + self.databaselist2):
            engine = db.get('engine')
            if engine:
                try:
                    with engine.connect() as conn:
                        for sql in migration_sql:
                            try:
                                conn.execute(text(sql))  # Execute each ALTER statement
                                conn.commit()  # Commit after each to avoid partial failures
                            except Exception as e:
                                # Ignore errors if column already exists (SQLite safe)
                                if "duplicate column name" not in str(e).lower():
                                    print(f"❌ Migration error for {db['name']}: {e}")
                        print(f"✅ Schema migrated for database: {db['name']}")
                except Exception as e:
                    print(f"❌ Error migrating {db['name']}: {e}")

    def test_database_connectivity(self, db_type: str = "backlink") -> bool:
        """
        Test database connectivity before performing large operations.
        Returns True if database is accessible and working.
        """
        print(f"🔍 Testing {db_type} database connectivity...")

        try:
            with self.get_session(db_type) as session:
                # Simple test query
                result = session.execute(text("SELECT 1")).scalar()
                if result == 1:
                    print(f"✅ {db_type.title()} database connection successful")
                    return True
                else:
                    print(f"❌ {db_type.title()} database connection test failed")
                    return False

        except Exception as e:
            print(f"❌ {db_type.title()} database connectivity test failed: {e}")
            return False

    # Crawl Session Methods
    def create_crawl_session(self, seed_urls: List[str], config_data: Dict) -> tuple[int, str]:
        """Create new crawl session and return (id, db_name)"""
        db = self._choose_db("crawl")
        if not db:
            raise RuntimeError("No available crawl database under quota")
        session = db['sessionmaker']()
        try:
            crawl_session = CrawlSession(
                seed_urls=str(seed_urls),
                config=str(config_data)
            )
            session.add(crawl_session)
            session.commit()
            session.refresh(crawl_session)
            return crawl_session.id, db['name']
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ Error creating crawl session: {e}")
            raise
        finally:
            session.close()

    def finish_crawl_session(self, session_id: str, status: str):
        """Finish crawl session"""
        with self.get_session("crawl") as session:
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

    # Enhanced: Crawled Pages with comprehensive data storage
    def store_crawled_page(self, page_data: Dict, session_id: int, db_name: str):
        """Store comprehensive crawled page data in the correct DB"""
        session = self.get_specific_db_session(db_name, "crawl")
        start_time = time.time()
        url = page_data.get('url', '')

        try:
            # Ensure the crawl session exists
            crawl_session = session.get(CrawlSession, session_id)
            if not crawl_session:
                raise ValueError(f"CrawlSession with id {session_id} does not exist in DB {db_name}.")

            # Check if URL already exists
            existing_page = session.execute(
                select(CrawledPage).where(CrawledPage.url == url)
            ).scalar_one_or_none()

            if existing_page:
                # Update existing record (keep original session_id)
                print(f"🔄 Updating existing page: {url}")
                log_db_operation("update", db_name, "crawled_pages", success=True)
                # Update fields but keep original session_id
                existing_page.title = page_data.get('title')
                existing_page.meta_description = page_data.get('meta_description')
                existing_page.content_text = page_data.get('content_text')
                existing_page.content_html = page_data.get('content_html')
                existing_page.content_hash = page_data.get('content_hash')
                existing_page.word_count = page_data.get('word_count')
                existing_page.page_size = page_data.get('page_size')
                existing_page.http_status_code = page_data.get('http_status_code')
                existing_page.response_time_ms = page_data.get('response_time_ms')
                existing_page.language = page_data.get('language')
                existing_page.charset = page_data.get('charset')
                existing_page.canonical_url = page_data.get('canonical_url')
                existing_page.robots_meta = page_data.get('robots_meta')
                existing_page.internal_links_count = page_data.get('internal_links_count')
                existing_page.external_links_count = page_data.get('external_links_count')
                existing_page.images_count = page_data.get('images_count')
                existing_page.content_type = page_data.get('content_type')
                existing_page.file_extension = page_data.get('file_extension')
            else:
                # Create new record
                # Handle redirect chain JSON conversion
                redirect_chain = page_data.get('redirect_chain', [])
                if isinstance(redirect_chain, list):
                    redirect_chain_str = str(redirect_chain)
                else:
                    redirect_chain_str = str(redirect_chain) if redirect_chain else None

                # Handle meta tags JSON conversion
                h1_tags = page_data.get('h1_tags', [])
                h2_tags = page_data.get('h2_tags', [])
                meta_keywords = page_data.get('meta_keywords', [])

                crawled_page = CrawledPage(
                    session_id=session_id,
                    url=url,
                    original_url=page_data.get('original_url'),
                    redirect_chain=redirect_chain_str,
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
                    h1_tags=str(h1_tags) if h1_tags else None,
                    h2_tags=str(h2_tags) if h2_tags else None,
                    meta_keywords=str(meta_keywords) if meta_keywords else None,
                    canonical_url=page_data.get('canonical_url'),
                    robots_meta=page_data.get('robots_meta'),
                    internal_links_count=page_data.get('internal_links_count'),
                    external_links_count=page_data.get('external_links_count'),
                    images_count=page_data.get('images_count'),
                    content_type=page_data.get('content_type'),
                    file_extension=page_data.get('file_extension')
                )
                session.add(crawled_page)
                print(f"✅ Stored crawled page: {url}")
                log_db_operation("insert", db_name, "crawled_pages", record_count=1, success=True)

            session.commit()
            duration = time.time() - start_time
            log_db_operation("commit", db_name, "crawled_pages", duration=duration, success=True)

        except SQLAlchemyError as e:
            session.rollback()
            duration = time.time() - start_time
            print(f"❌ Error storing crawled page: {e}")
            log_db_operation("store_page", db_name, "crawled_pages", duration=duration, success=False, error=str(e))
            raise
        except Exception as e:
            session.rollback()
            duration = time.time() - start_time
            print(f"❌ Error storing crawled page: {e}")
            log_db_operation("store_page", db_name, "crawled_pages", duration=duration, success=False, error=str(e))
            raise
        finally:
            session.close()

    # Enhanced: Backlinks with better error handling and optimized batch processing
    def store_backlinks(self, backlinks: List[Any]):
        """Store backlinks in DB (round-robin backlink DBs) with optimized batch processing"""
        if not backlinks:
            return

        total_backlinks = len(backlinks)
        print(f"📦 Starting to store {total_backlinks:,} backlinks...")

        # Use larger chunks for better performance with large datasets
        chunk_size = 5000  # Process 5000 at a time
        stored_count = 0

        for i in range(0, total_backlinks, chunk_size):
            chunk = backlinks[i:i + chunk_size]
            chunk_num = (i // chunk_size) + 1
            total_chunks = (total_backlinks + chunk_size - 1) // chunk_size

            print(f"📝 Processing chunk {chunk_num}/{total_chunks} ({len(chunk):,} backlinks)...")

            # Use a fresh session for each chunk to avoid memory buildup
            with self.get_session("backlink") as session:
                try:
                    chunk_stored = 0
                    batch_objects = []

                    for backlink in chunk:
                        if hasattr(backlink, 'source_url') and hasattr(backlink, 'target_url'):
                            db_backlink = Backlink(
                                source_url=backlink.source_url,
                                target_url=backlink.target_url,
                                anchor_text=getattr(backlink, 'anchor_text', ''),
                                context=getattr(backlink, 'context', ''),
                                page_title=getattr(backlink, 'page_title', ''),
                                domain_authority=getattr(backlink, 'domain_authority', 0.0),
                                is_nofollow=getattr(backlink, 'is_nofollow', False)
                            )
                            batch_objects.append(db_backlink)
                            chunk_stored += 1

                    # Bulk insert the entire chunk at once
                    if batch_objects:
                        session.add_all(batch_objects)
                        session.commit()
                        stored_count += chunk_stored

                        print(f"✅ Chunk {chunk_num} complete: {chunk_stored:,} backlinks stored "
                              f"({stored_count:,}/{total_backlinks:,} total - "
                              f"{(stored_count/total_backlinks)*100:.1f}%)")

                except SQLAlchemyError as e:
                    session.rollback()
                    print(f"❌ Error storing chunk {chunk_num}: {e}")
                    print(f"⚠️  Continuing with next chunk...")
                    continue  # Continue with next chunk instead of failing completely
                except Exception as e:
                    session.rollback()
                    print(f"❌ Unexpected error in chunk {chunk_num}: {e}")
                    print(f"⚠️  Continuing with next chunk...")
                    continue

        print(f"🎉 Backlink storage complete! Total stored: {stored_count:,}/{total_backlinks:,} backlinks")

        if stored_count < total_backlinks:
            failed_count = total_backlinks - stored_count
            print(f"⚠️  Warning: {failed_count:,} backlinks failed to store due to errors")

    def store_domain_scores(self, domain_scores: Dict[str, float]):
        """Store or update domain authority scores with optimized batch processing"""
        if not domain_scores:
            return

        total_domains = len(domain_scores)
        print(f"📊 Starting to store {total_domains:,} domain authority scores...")

        # Process in chunks for better performance
        chunk_size = 1000
        domain_items = list(domain_scores.items())
        stored_count = 0

        for i in range(0, total_domains, chunk_size):
            chunk = domain_items[i:i + chunk_size]
            chunk_num = (i // chunk_size) + 1
            total_chunks = (total_domains + chunk_size - 1) // chunk_size

            print(f"📝 Processing domain chunk {chunk_num}/{total_chunks} ({len(chunk):,} domains)...")

            with self.get_session("backlink") as session:
                try:
                    chunk_stored = 0
                    batch_updates = []
                    batch_inserts = []

                    for domain, score in chunk:
                        # Check if domain already exists
                        existing_domain = session.execute(
                            select(DomainAuthority).where(DomainAuthority.domain == domain)
                        ).scalar_one_or_none()

                        if existing_domain:
                            # Prepare update operation
                            batch_updates.append({
                                'domain': domain,
                                'authority_score': score,
                                'last_updated': datetime.now()
                            })
                        else:
                            # Prepare insert operation
                            batch_inserts.append(DomainAuthority(
                                domain=domain,
                                authority_score=score
                            ))

                        chunk_stored += 1

                    # Execute batch updates
                    if batch_updates:
                        for update_data in batch_updates:
                            session.execute(
                                update(DomainAuthority)
                                .where(DomainAuthority.domain == update_data['domain'])
                                .values(
                                    authority_score=update_data['authority_score'],
                                    last_updated=update_data['last_updated']
                                )
                            )

                    # Execute batch inserts
                    if batch_inserts:
                        session.add_all(batch_inserts)

                    session.commit()
                    stored_count += chunk_stored

                    print(f"✅ Domain chunk {chunk_num} complete: {chunk_stored:,} domains processed "
                          f"({stored_count:,}/{total_domains:,} total - "
                          f"{(stored_count/total_domains)*100:.1f}%)")

                except SQLAlchemyError as e:
                    session.rollback()
                    print(f"❌ Error storing domain chunk {chunk_num}: {e}")
                    print(f"⚠️  Continuing with next chunk...")
                    continue
                except Exception as e:
                    session.rollback()
                    print(f"❌ Unexpected error in domain chunk {chunk_num}: {e}")
                    print(f"⚠️  Continuing with next chunk...")
                    continue

        print(f"🎉 Domain scores storage complete! Total processed: {stored_count:,}/{total_domains:,} domains")

    def store_pagerank_scores(self, pagerank_scores: Dict[str, float]):
        """Store or update PageRank scores"""
        if not pagerank_scores:
            return

        with self.get_session("crawl") as session:
            try:
                stored_count = 0
                for url, score in pagerank_scores.items():
                    # Check if URL already exists
                    existing_score = session.execute(
                        select(PageRankScore).where(PageRankScore.url == url)
                    ).scalar_one_or_none()

                    if existing_score:
                        # Update existing record using update statement
                        session.execute(
                            update(PageRankScore)
                            .where(PageRankScore.url == url)
                            .values(pagerank_score=score, last_calculated=datetime.now())
                        )
                    else:
                        # Create new record
                        pagerank_score = PageRankScore(
                            url=url,
                            pagerank_score=score
                        )
                        session.add(pagerank_score)

                    stored_count += 1

                    # Batch commit every 100 records
                    if stored_count % 100 == 0:
                        session.commit()

                session.commit()  # Final commit
                print(f"✅ Stored/updated {stored_count} PageRank scores")
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error storing PageRank scores: {e}")
                raise

    def store_crawl_error(self, error_data: Dict, session_id: str):
        """Store crawl errors"""
        with self.get_session("crawl") as session:
            try:
                crawl_error = CrawlError(
                    session_id=int(session_id),
                    url=error_data.get('url', ''),
                    error_type=error_data.get('error_type', ''),
                    error_msg=error_data.get('error_msg', ''),
                    status_code=error_data.get('status_code')
                )
                session.add(crawl_error)
                session.commit()
                print(f"✅ Stored crawl error for: {error_data.get('url', 'Unknown')}")
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error storing crawl error: {e}")
                raise

    def get_crawl_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a crawl session"""
        with self.get_session("crawl") as session:
            try:
                # Get session info
                crawl_session = session.execute(
                    select(CrawlSession).where(CrawlSession.id == int(session_id))
                ).scalar_one_or_none()

                if not crawl_session:
                    return {"error": "Session not found"}

                # Count crawled pages
                pages_count = session.execute(
                    select(func.count(CrawledPage.id)).where(CrawledPage.session_id == int(session_id))
                ).scalar() or 0

                # Count errors
                errors_count = session.execute(
                    select(func.count(CrawlError.id)).where(CrawlError.session_id == int(session_id))
                ).scalar() or 0

                return {
                    "session_id": session_id,
                    "status": crawl_session.status,
                    "start_time": crawl_session.start_time,
                    "end_time": crawl_session.end_time,
                    "pages_crawled": pages_count,
                    "errors_count": errors_count
                }
            except SQLAlchemyError as e:
                print(f"❌ Error getting session stats: {e}")
                return {"error": str(e)}

    def get_domain_authority_scores(self) -> Dict[str, float]:
        """Get all domain authority scores"""
        with self.get_session("backlink") as session:
            try:
                domain_authorities = session.execute(select(DomainAuthority)).scalars().all()
                return {da.domain: da.authority_score for da in domain_authorities}
            except SQLAlchemyError as e:
                print(f"❌ Error getting domain authority scores: {e}")
                return {}

    def get_discovered_subdomains(self) -> List[str]:
        """Get discovered subdomains from crawled pages"""
        with self.get_session("crawl") as session:
            try:
                from urllib.parse import urlparse
                pages = session.execute(select(CrawledPage.url)).scalars().all()

                subdomains = set()
                for url in pages:
                    parsed = urlparse(url)
                    domain = parsed.netloc
                    if domain.count('.') > 1:  # Has subdomain
                        subdomains.add(f"https://{domain}")

                return list(subdomains)
            except SQLAlchemyError as e:
                print(f"❌ Error getting subdomains: {e}")
                return []

    def get_all_backlinks(self) -> List[Dict]:
        """Get all backlinks from database"""
        with self.get_session("backlink") as session:
            try:
                backlinks = session.execute(select(Backlink)).scalars().all()
                return [
                    {
                        'source_url': bl.source_url,
                        'target_url': bl.target_url,
                        'anchor_text': bl.anchor_text,
                        'is_nofollow': bl.is_nofollow,
                        'domain_authority': bl.domain_authority
                    }
                    for bl in backlinks
                ]
            except SQLAlchemyError as e:
                print(f"❌ Error getting backlinks: {e}")
                return []

    def get_all_crawled_urls(self) -> List[str]:
        """Get all crawled URLs"""
        with self.get_session("crawl") as session:
            try:
                urls = session.execute(select(CrawledPage.url)).scalars().all()
                return list(urls)
            except SQLAlchemyError as e:
                print(f"❌ Error getting crawled URLs: {e}")
                return []

    def get_pagerank_scores(self) -> Dict[str, float]:
        """Get all PageRank scores"""
        with self.get_session("crawl") as session:
            try:
                pageranks = session.execute(select(PageRankScore)).scalars().all()
                return {pr.url: pr.pagerank_score for pr in pageranks}
            except SQLAlchemyError as e:
                print(f"❌ Error getting PageRank scores: {e}")
                return {}

    def get_all_content_hashes(self) -> List[str]:
        """Get all content hashes to avoid duplicate content"""
        with self.get_session("crawl") as session:
            try:
                hashes = session.execute(
                    select(CrawledPage.content_hash).where(CrawledPage.content_hash.isnot(None))
                ).scalars().all()
                return [h for h in hashes if h is not None]
            except SQLAlchemyError as e:
                print(f"❌ Error getting content hashes: {e}")
                return []

    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Clean up old data older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleanup_count = 0

        # Clean old crawled pages
        with self.get_session("crawl") as session:
            try:
                result = session.execute(
                    delete(CrawledPage).where(CrawledPage.crawl_time < cutoff_date)
                )
                cleanup_count += result.rowcount
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error cleaning crawled pages: {e}")

        # Clean old backlinks
        with self.get_session("backlink") as session:
            try:
                result = session.execute(
                    delete(Backlink).where(Backlink.crawl_date < cutoff_date)
                )
                cleanup_count += result.rowcount
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                print(f"❌ Error cleaning backlinks: {e}")

        return cleanup_count

    def get_recent_backlinks(self, hours: int = 24) -> List[Dict]:
        """Get recent backlinks within specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self.get_session("backlink") as session:
            try:
                backlinks = session.execute(
                    select(Backlink).where(Backlink.crawl_date >= cutoff_time)
                ).scalars().all()

                return [
                    {
                        'source_url': bl.source_url,
                        'target_url': bl.target_url,
                        'anchor_text': bl.anchor_text,
                        'crawl_date': bl.crawl_date
                    }
                    for bl in backlinks
                ]
            except SQLAlchemyError as e:
                print(f"❌ Error getting recent backlinks: {e}")
                return []

    def get_crawl_session_by_id(self, session_id: int) -> Optional[Dict]:
        """Get crawl session details by ID"""
        with self.get_session("crawl") as session:
            try:
                crawl_session = session.execute(
                    select(CrawlSession).where(CrawlSession.id == session_id)
                ).scalar_one_or_none()

                if not crawl_session:
                    return None

                return {
                    "id": crawl_session.id,
                    "seed_urls": crawl_session.seed_urls,
                    "config": crawl_session.config,
                    "start_time": crawl_session.start_time,
                    "end_time": crawl_session.end_time,
                    "status": crawl_session.status
                }
            except SQLAlchemyError as e:
                print(f"❌ Error getting crawl session: {e}")
                return None

    def get_pages_by_session(self, session_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get crawled pages for a specific session with pagination"""
        with self.get_session("crawl") as session:
            try:
                pages = session.execute(
                    select(CrawledPage)
                    .where(CrawledPage.session_id == session_id)
                    .limit(limit)
                    .offset(offset)
                ).scalars().all()

                return [
                    {
                        "id": page.id,
                        "url": page.url,
                        "title": page.title,
                        "http_status_code": page.http_status_code,
                        "word_count": page.word_count,
                        "crawl_time": page.crawl_time,
                        "content_hash": page.content_hash
                    }
                    for page in pages
                ]
            except SQLAlchemyError as e:
                print(f"❌ Error getting pages by session: {e}")
                return []

    def get_backlinks_by_domain(self, domain: str) -> List[Dict]:
        """Get all backlinks for a specific domain"""
        with self.get_session("backlink") as session:
            try:
                backlinks = session.execute(
                    select(Backlink).where(Backlink.target_url.like(f"%{domain}%"))
                ).scalars().all()

                return [
                    {
                        'id': bl.id,
                        'source_url': bl.source_url,
                        'target_url': bl.target_url,
                        'anchor_text': bl.anchor_text,
                        'context': bl.context,
                        'page_title': bl.page_title,
                        'domain_authority': bl.domain_authority,
                        'is_nofollow': bl.is_nofollow,
                        'crawl_date': bl.crawl_date
                    }
                    for bl in backlinks
                ]
            except SQLAlchemyError as e:
                print(f"❌ Error getting backlinks by domain: {e}")
                return []

    def search_pages_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict]:
        """Search crawled pages by keyword in title or content"""
        with self.get_session("crawl") as session:
            try:
                pages = session.execute(
                    select(CrawledPage)
                    .where(
                        CrawledPage.title.like(f"%{keyword}%") |
                        CrawledPage.content_text.like(f"%{keyword}%")
                    )
                    .limit(limit)
                ).scalars().all()

                return [
                    {
                        "id": page.id,
                        "url": page.url,
                        "title": page.title,
                        "meta_description": page.meta_description,
                        "word_count": page.word_count,
                        "crawl_time": page.crawl_time
                    }
                    for page in pages
                ]
            except SQLAlchemyError as e:
                print(f"❌ Error searching pages by keyword: {e}")
                return []

    def get_database_statistics(self) -> Dict:
        """Get comprehensive database statistics"""
        stats = {
            "crawl_stats": {},
            "backlink_stats": {},
            "database_health": self.get_database_health_status()
        }

        # Crawl database statistics
        try:
            with self.get_session("crawl") as session:
                # Count total sessions
                total_sessions = session.execute(select(func.count(CrawlSession.id))).scalar() or 0

                # Count total pages
                total_pages = session.execute(select(func.count(CrawledPage.id))).scalar() or 0

                # Count total errors
                total_errors = session.execute(select(func.count(CrawlError.id))).scalar() or 0

                # Get recent activity (last 24 hours)
                recent_cutoff = datetime.now() - timedelta(hours=24)
                recent_pages = session.execute(
                    select(func.count(CrawledPage.id))
                    .where(CrawledPage.crawl_time >= recent_cutoff)
                ).scalar() or 0

                stats["crawl_stats"] = {
                    "total_sessions": total_sessions,
                    "total_pages": total_pages,
                    "total_errors": total_errors,
                    "recent_pages_24h": recent_pages
                }
        except SQLAlchemyError as e:
            print(f"❌ Error getting crawl stats: {e}")
            stats["crawl_stats"] = {"error": str(e)}

        # Backlink database statistics
        try:
            with self.get_session("backlink") as session:
                # Count total backlinks
                total_backlinks = session.execute(select(func.count(Backlink.id))).scalar() or 0

                # Count total domains
                total_domains = session.execute(select(func.count(DomainAuthority.id))).scalar() or 0

                # Get recent backlinks (last 24 hours)
                recent_cutoff = datetime.now() - timedelta(hours=24)
                recent_backlinks = session.execute(
                    select(func.count(Backlink.id))
                    .where(Backlink.crawl_date >= recent_cutoff)
                ).scalar() or 0

                stats["backlink_stats"] = {
                    "total_backlinks": total_backlinks,
                    "total_domains": total_domains,
                    "recent_backlinks_24h": recent_backlinks
                }
        except SQLAlchemyError as e:
            print(f"❌ Error getting backlink stats: {e}")
            stats["backlink_stats"] = {"error": str(e)}

        return stats

    def execute_custom_query(self, query: str, db_type: str = "crawl", params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a custom SQL query on specified database type.
        WARNING: Use with caution - only for read operations.
        """
        if not query.strip().upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed for security reasons")

        with self.get_session(db_type) as session:
            try:
                result = session.execute(text(query), params or {})

                # Convert result to list of dictionaries
                columns = result.keys()
                rows = result.fetchall()

                return [dict(zip(columns, row)) for row in rows]
            except SQLAlchemyError as e:
                print(f"❌ Error executing custom query: {e}")
                return []

    def bulk_update_pages(self, updates: List[Dict], db_name: Optional[str] = None):
        """
        Bulk update crawled pages.
        updates: List of dicts with 'url' and fields to update
        """
        session = (self.get_specific_db_session(db_name, "crawl") if db_name
                  else self.get_session("crawl"))

        try:
            updated_count = 0
            for update_data in updates:
                url = update_data.pop('url')  # Remove URL from update data

                result = session.execute(
                    update(CrawledPage)
                    .where(CrawledPage.url == url)
                    .values(**update_data)
                )

                if result.rowcount > 0:
                    updated_count += 1

                # Batch commit every 100 updates
                if updated_count % 100 == 0:
                    session.commit()

            session.commit()  # Final commit
            print(f"✅ Bulk updated {updated_count} pages")

        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ Error in bulk update: {e}")
            raise
        finally:
            session.close()

    def get_pages_by_status_code(self, status_code: int) -> List[Dict]:
        """Get pages by HTTP status code"""
        with self.get_session("crawl") as session:
            try:
                pages = session.execute(
                    select(CrawledPage).where(CrawledPage.http_status_code == status_code)
                ).scalars().all()

                return [
                    {
                        "url": page.url,
                        "title": page.title,
                        "status_code": page.http_status_code,
                        "crawl_time": page.crawl_time,
                        "response_time_ms": page.response_time_ms
                    }
                    for page in pages
                ]
            except SQLAlchemyError as e:
                print(f"❌ Error getting pages by status code: {e}")
                return []

    def get_high_authority_backlinks(self, min_authority: float = 50.0) -> List[Dict]:
        """Get backlinks from high authority domains"""
        with self.get_session("backlink") as session:
            try:
                backlinks = session.execute(
                    select(Backlink).where(Backlink.domain_authority >= min_authority)
                ).scalars().all()

                return [
                    {
                        'source_url': bl.source_url,
                        'target_url': bl.target_url,
                        'anchor_text': bl.anchor_text,
                        'domain_authority': bl.domain_authority,
                        'is_nofollow': bl.is_nofollow,
                        'crawl_date': bl.crawl_date
                    }
                    for bl in backlinks
                ]
            except SQLAlchemyError as e:
                print(f"❌ Error getting high authority backlinks: {e}")
                return []

    def migrate_data_between_dbs(self, source_db_name: str, target_db_name: str,
                                data_type: str, limit: int = 1000):
        """
        Migrate data between databases (for load balancing)
        data_type: 'pages', 'backlinks', 'sessions'
        """
        db_type = "crawl" if data_type in ["pages", "sessions"] else "backlink"

        source_session = self.get_specific_db_session(source_db_name, db_type)
        target_session = self.get_specific_db_session(target_db_name, db_type)

        try:
            migrated_count = 0

            if data_type == "pages":
                # Migrate oldest pages first
                pages = source_session.execute(
                    select(CrawledPage)
                    .order_by(CrawledPage.crawl_time)
                    .limit(limit)
                ).scalars().all()

                for page in pages:
                    # Create new page in target DB
                    new_page = CrawledPage(
                        session_id=page.session_id,
                        url=page.url,
                        original_url=page.original_url,
                        redirect_chain=page.redirect_chain,
                        title=page.title,
                        meta_description=page.meta_description,
                        content_text=page.content_text,
                        content_html=page.content_html,
                        content_hash=page.content_hash,
                        word_count=page.word_count,
                        page_size=page.page_size,
                        http_status_code=page.http_status_code,
                        response_time_ms=page.response_time_ms,
                        language=page.language,
                        charset=page.charset,
                        h1_tags=page.h1_tags,
                        h2_tags=page.h2_tags,
                        meta_keywords=page.meta_keywords,
                        canonical_url=page.canonical_url,
                        robots_meta=page.robots_meta,
                        internal_links_count=page.internal_links_count,
                        external_links_count=page.external_links_count,
                        images_count=page.images_count,
                        crawl_time=page.crawl_time
                    )
                    target_session.add(new_page)
                    migrated_count += 1

                # Commit new pages
                target_session.commit()

                # Delete old pages
                for page in pages:
                    source_session.delete(page)
                source_session.commit()

            elif data_type == "backlinks":
                # Migrate oldest backlinks first
                backlinks = source_session.execute(
                    select(Backlink)
                    .order_by(Backlink.crawl_date)
                    .limit(limit)
                ).scalars().all()

                for backlink in backlinks:
                    new_backlink = Backlink(
                        source_url=backlink.source_url,
                        target_url=backlink.target_url,
                        anchor_text=backlink.anchor_text,
                        context=backlink.context,
                        page_title=backlink.page_title,
                        domain_authority=backlink.domain_authority,
                        is_nofollow=backlink.is_nofollow,
                        crawl_date=backlink.crawl_date
                    )
                    target_session.add(new_backlink)
                    migrated_count += 1

                # Commit new backlinks
                target_session.commit()

                # Delete old backlinks
                for backlink in backlinks:
                    source_session.delete(backlink)
                source_session.commit()

            print(f"✅ Migrated {migrated_count} {data_type} from {source_db_name} to {target_db_name}")
            return migrated_count

        except SQLAlchemyError as e:
            source_session.rollback()
            target_session.rollback()
            print(f"❌ Error migrating data: {e}")
            raise
        finally:
            source_session.close()
            target_session.close()

    def refresh_database_cycles(self):
        """Refresh the round-robin cycles (useful after adding/removing databases)"""
        self.health.useabledbdata()  # Refresh useable databases

        # Update database lists
        self.crwlDB = self.health.useable_databases_crawler
        self.bcklDB = self.health.useable_databases_backlink

        # Clear and rebuild engine lists
        self.databaselist1.clear()
        self.databaselist2.clear()
        self.__enginelist()

        # Recreate cycles
        self._cycle_crawl = itertools.cycle(self.databaselist1) if self.databaselist1 else None
        self._cycle_backlink = itertools.cycle(self.databaselist2) if self.databaselist2 else None

        print(f"✅ Refreshed database cycles - Crawl DBs: {len(self.databaselist1)}, Backlink DBs: {len(self.databaselist2)}")

    def test_database_connections(self) -> Dict:
        """Test all database connections"""
        results = {
            "crawl_databases": {},
            "backlink_databases": {},
            "summary": {
                "total_crawl": len(self.databaselist1),
                "working_crawl": 0,
                "total_backlink": len(self.databaselist2),
                "working_backlink": 0
            }
        }

        # Test crawl databases
        for db in self.databaselist1:
            try:
                session = db['sessionmaker']()
                # Simple test query
                session.execute(select(func.count(CrawlSession.id)))
                session.close()
                results["crawl_databases"][db['name']] = {"status": "OK", "error": None}
                results["summary"]["working_crawl"] += 1
            except Exception as e:
                results["crawl_databases"][db['name']] = {"status": "ERROR", "error": str(e)}

        # Test backlink databases
        for db in self.databaselist2:
            try:
                session = db['sessionmaker']()
                # Simple test query
                session.execute(select(func.count(Backlink.id)))
                session.close()
                results["backlink_databases"][db['name']] = {"status": "OK", "error": None}
                results["summary"]["working_backlink"] += 1
            except Exception as e:
                results["backlink_databases"][db['name']] = {"status": "ERROR", "error": str(e)}

        return results

    def force_quota_refresh(self):
        """Force refresh of quota information for all databases"""
        print("🔄 Forcing quota refresh for all databases...")

        refreshed_count = 0
        for db in self.databaselist1 + self.databaselist2:
            try:
                usage = self.health.current_limit(db['name'], db['organization'], db['apikey'])
                if usage:
                    refreshed_count += 1
                    print(f"✅ Refreshed quota for {db['name']}: {usage.get('storage_bytes', 0)} bytes, {usage.get('rows_written', 0)} writes")
            except Exception as e:
                print(f"❌ Error refreshing quota for {db['name']}: {e}")

        print(f"✅ Quota refresh complete for {refreshed_count} databases")

    def get_database_by_name(self, db_name: str) -> Optional[Dict]:
        """Get database configuration by name"""
        all_dbs = self.databaselist1 + self.databaselist2
        return next((db for db in all_dbs if db['name'] == db_name), None)

    def close(self):
        """Close all DB connections"""
        for db in (self.databaselist1 + self.databaselist2):
            engine = db.get('engine')
            if engine:
                engine.dispose()
        print("✅ All database connections closed")
