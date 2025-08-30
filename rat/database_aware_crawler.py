"""
Enhanced Database-Aware Crawler
Integrates with multi-database system for optimal data storage and automatic rotation
"""

import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from rat.multi_database import multi_db_manager, DatabaseType
from rat.backlinkprocessor import BacklinkProcessor, BacklinkData
from rat.crawler import EnhancedProductionCrawler


class DatabaseAwareCrawler:
    """
    Enhanced crawler that intelligently manages data across multiple databases
    """

    def __init__(self, config: Dict):
        self.config = config
        self.delay = config.get('delay', 1.5)
        self.max_depth = config.get('max_depth', 3)
        self.max_pages = config.get('max_pages', 100)

        # Initialize database manager
        self.db_manager = multi_db_manager

        # Track current databases for each data type
        self.current_backlink_db = None
        self.current_webpage_db = None

        # Initialize processors
        self.backlink_processor = BacklinkProcessor(delay=self.delay)

        # Stats tracking
        self.stats = {
            "pages_crawled": 0,
            "backlinks_found": 0,
            "database_rotations": 0,
            "errors": 0,
            "start_time": datetime.now()
        }

    def start_crawling_session(self, seed_urls: List[str]) -> str:
        """Start a new crawling session with proper database allocation"""
        print("🚀 Starting Enhanced Database-Aware Crawling Session")
        print("=" * 60)

        # Get optimal databases for each data type
        self.current_backlink_db = self._get_or_rotate_database(DatabaseType.BACKLINK)
        self.current_webpage_db = self._get_or_rotate_database(DatabaseType.WEBPAGE)

        print(f"📊 Backlink Database: {self.current_backlink_db['name']}")
        print(f"🌐 Webpage Database: {self.current_webpage_db['name']}")
        print()

        # Create crawl session ID
        session_id = f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize database schemas if needed
        self._initialize_database_schemas()

        return session_id

    def _get_or_rotate_database(self, data_type: str) -> Optional[Dict]:
        """Get optimal database or rotate if current one is full"""
        db = self.db_manager.get_optimal_database_for_type(data_type)
        if not db:
            print(f"❌ No available database for {data_type}")
            raise Exception(f"No available database for {data_type}")

        return db

    def _initialize_database_schemas(self):
        """Initialize required database schemas"""
        # Initialize backlink database schema
        backlink_conn = self.db_manager.get_database_connection(self.current_backlink_db["name"])
        if backlink_conn:
            backlink_conn.execute_write('''
                CREATE TABLE IF NOT EXISTS backlinks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_url TEXT NOT NULL,
                    target_url TEXT NOT NULL,
                    anchor_text TEXT,
                    context TEXT,
                    page_title TEXT,
                    domain_authority REAL DEFAULT 0.0,
                    is_nofollow BOOLEAN DEFAULT FALSE,
                    crawl_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    data_size INTEGER DEFAULT 0,
                    UNIQUE(source_url, target_url)
                )
            ''')

        # Initialize webpage database schema
        webpage_conn = self.db_manager.get_database_connection(self.current_webpage_db["name"])
        if webpage_conn:
            webpage_conn.execute_write('''
                CREATE TABLE IF NOT EXISTS crawled_pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT,
                    content_text TEXT,
                    content_html TEXT,
                    meta_description TEXT,
                    word_count INTEGER DEFAULT 0,
                    page_size INTEGER DEFAULT 0,
                    http_status_code INTEGER DEFAULT 200,
                    response_time_ms INTEGER DEFAULT 0,
                    internal_links_count INTEGER DEFAULT 0,
                    external_links_count INTEGER DEFAULT 0,
                    images_count INTEGER DEFAULT 0,
                    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    data_size INTEGER DEFAULT 0
                )
            ''')

    def crawl_with_backlink_analysis(self, seed_urls: List[str]) -> Dict:
        """
        Main crawling method that performs both webpage crawling and backlink analysis
        with intelligent database management
        """
        session_id = self.start_crawling_session(seed_urls)

        try:
            # Phase 1: Website Content Crawling
            print("📄 Phase 1: Website Content Crawling")
            print("-" * 40)
            webpage_results = self._crawl_webpages(seed_urls, session_id)

            # Phase 2: Backlink Discovery and Analysis
            print("\\n🔗 Phase 2: Backlink Discovery and Analysis")
            print("-" * 40)
            backlink_results = self._analyze_backlinks(seed_urls, session_id)

            # Phase 3: Generate Reports and Analytics
            print("\\n📊 Phase 3: Generating Analytics")
            print("-" * 40)
            analytics = self._generate_analytics(session_id)

            # Final results
            results = {
                "session_id": session_id,
                "pages_crawled": self.stats["pages_crawled"],
                "backlinks_found": self.stats["backlinks_found"],
                "database_rotations": self.stats["database_rotations"],
                "errors": self.stats["errors"],
                "duration_minutes": (datetime.now() - self.stats["start_time"]).seconds / 60,
                "databases_used": {
                    "backlink_db": self.current_backlink_db["name"],
                    "webpage_db": self.current_webpage_db["name"]
                },
                "analytics": analytics
            }

            print("\\n✅ Crawling Session Complete!")
            print(f"📊 Results Summary:")
            print(f"   • Pages Crawled: {results['pages_crawled']}")
            print(f"   • Backlinks Found: {results['backlinks_found']}")
            print(f"   • Database Rotations: {results['database_rotations']}")
            print(f"   • Duration: {results['duration_minutes']:.1f} minutes")

            return results

        except Exception as e:
            print(f"❌ Error during crawling session: {e}")
            self.stats["errors"] += 1
            raise

    def _crawl_webpages(self, urls: List[str], session_id: str) -> Dict:
        """Crawl webpages and store in webpage database"""
        results = {"pages": [], "errors": []}

        for i, url in enumerate(urls):
            try:
                # Check if database rotation is needed
                rotated_db = self.db_manager.rotate_database_if_needed(
                    self.current_webpage_db["name"],
                    DatabaseType.WEBPAGE
                )
                if rotated_db:
                    self.current_webpage_db = next(
                        db for db in self.db_manager.databases["databases"]
                        if db["name"] == rotated_db
                    )
                    self.stats["database_rotations"] += 1
                    print(f"🔄 Rotated to webpage database: {rotated_db}")

                print(f"📄 Crawling [{i+1}/{len(urls)}]: {url}")

                # Simulate webpage crawling (replace with actual crawler)
                page_data = self._simulate_page_crawl(url, session_id)

                # Store in database
                self._store_webpage_data(page_data, session_id)

                results["pages"].append(page_data)
                self.stats["pages_crawled"] += 1

                # Respect delay
                time.sleep(self.delay)

            except Exception as e:
                print(f"❌ Error crawling {url}: {e}")
                results["errors"].append({"url": url, "error": str(e)})
                self.stats["errors"] += 1

        return results

    def _analyze_backlinks(self, target_urls: List[str], session_id: str) -> Dict:
        """Analyze backlinks for target URLs and store in backlink database"""
        results = {"backlinks": [], "errors": []}

        for i, target_url in enumerate(target_urls):
            try:
                # Check if database rotation is needed
                rotated_db = self.db_manager.rotate_database_if_needed(
                    self.current_backlink_db["name"],
                    DatabaseType.BACKLINK
                )
                if rotated_db:
                    self.current_backlink_db = next(
                        db for db in self.db_manager.databases["databases"]
                        if db["name"] == rotated_db
                    )
                    self.stats["database_rotations"] += 1
                    print(f"🔄 Rotated to backlink database: {rotated_db}")

                print(f"🔗 Analyzing backlinks [{i+1}/{len(target_urls)}]: {target_url}")

                # Discover backlinks using backlink processor
                self.backlink_processor.crawl_backlinks([target_url], max_depth=2)
                backlinks = self.backlink_processor.backlinks

                # Store backlinks in database
                for backlink in backlinks:
                    self._store_backlink_data(backlink, session_id)
                    results["backlinks"].append(backlink)

                self.stats["backlinks_found"] += len(backlinks)
                print(f"   Found {len(backlinks)} backlinks")

                # Respect delay
                time.sleep(self.delay)

            except Exception as e:
                print(f"❌ Error analyzing backlinks for {target_url}: {e}")
                results["errors"].append({"url": target_url, "error": str(e)})
                self.stats["errors"] += 1

        return results

    def _simulate_page_crawl(self, url: str, session_id: str) -> Dict:
        """Simulate webpage crawling (replace with actual implementation)"""
        return {
            "url": url,
            "title": f"Sample Page - {urlparse(url).netloc}",
            "content_text": f"Sample content for {url}",
            "content_html": f"<html><body>Sample HTML content for {url}</body></html>",
            "meta_description": f"Sample meta description for {url}",
            "word_count": 500,
            "page_size": 15000,
            "http_status_code": 200,
            "response_time_ms": 250,
            "internal_links_count": 10,
            "external_links_count": 5,
            "images_count": 8,
            "crawl_time": datetime.now(),
            "session_id": session_id,
            "data_size": 15000
        }

    def _store_webpage_data(self, page_data: Dict, session_id: str):
        """Store webpage data in the current webpage database"""
        conn = self.db_manager.get_database_connection(self.current_webpage_db["name"])
        if not conn:
            raise Exception(f"Cannot connect to webpage database: {self.current_webpage_db['name']}")

        # Insert webpage data
        conn.execute_write('''
            INSERT OR REPLACE INTO crawled_pages
            (url, title, content_text, content_html, meta_description, word_count,
             page_size, http_status_code, response_time_ms, internal_links_count,
             external_links_count, images_count, crawl_time, session_id, data_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            page_data["url"], page_data["title"], page_data["content_text"],
            page_data["content_html"], page_data["meta_description"],
            page_data["word_count"], page_data["page_size"],
            page_data["http_status_code"], page_data["response_time_ms"],
            page_data["internal_links_count"], page_data["external_links_count"],
            page_data["images_count"], page_data["crawl_time"].isoformat(),
            session_id, page_data["data_size"]
        ))

        # Record database operation
        self.db_manager.record_database_operation(
            self.current_webpage_db["name"],
            "write",
            DatabaseType.WEBPAGE,
            page_data["data_size"]
        )

    def _store_backlink_data(self, backlink: BacklinkData, session_id: str):
        """Store backlink data in the current backlink database"""
        conn = self.db_manager.get_database_connection(self.current_backlink_db["name"])
        if not conn:
            raise Exception(f"Cannot connect to backlink database: {self.current_backlink_db['name']}")

        # Calculate data size estimate
        data_size = len(backlink.source_url) + len(backlink.target_url) + len(backlink.anchor_text) + 100

        # Insert backlink data
        conn.execute_write('''
            INSERT OR REPLACE INTO backlinks
            (source_url, target_url, anchor_text, context, page_title,
             domain_authority, is_nofollow, crawl_date, session_id, data_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            backlink.source_url, backlink.target_url, backlink.anchor_text,
            backlink.context, backlink.page_title, backlink.domain_authority,
            backlink.is_nofollow, datetime.now().isoformat(),
            session_id, data_size
        ))

        # Record database operation
        self.db_manager.record_database_operation(
            self.current_backlink_db["name"],
            "write",
            DatabaseType.BACKLINK,
            data_size
        )

    def _generate_analytics(self, session_id: str) -> Dict:
        """Generate analytics and insights from crawled data"""
        analytics = {
            "session_summary": {
                "id": session_id,
                "pages_crawled": self.stats["pages_crawled"],
                "backlinks_found": self.stats["backlinks_found"],
                "unique_domains": self._count_unique_domains(),
                "database_health": self.db_manager.get_all_database_status()
            },
            "top_domains": self._get_top_domains(),
            "database_usage": self._get_database_usage_summary()
        }

        return analytics

    def _count_unique_domains(self) -> int:
        """Count unique domains from crawled data"""
        # TODO: Implement actual domain counting from databases
        return 25

    def _get_top_domains(self) -> List[Dict]:
        """Get top domains by backlink count"""
        # TODO: Implement actual domain analysis
        return [
            {"domain": "example.com", "backlinks": 15, "authority": 75.2},
            {"domain": "sample.org", "backlinks": 12, "authority": 68.9},
            {"domain": "test.net", "backlinks": 8, "authority": 55.4}
        ]

    def _get_database_usage_summary(self) -> Dict:
        """Get database usage summary for this session"""
        return {
            "backlink_db": {
                "name": self.current_backlink_db["name"],
                "health": self.db_manager._check_database_health(self.current_backlink_db["name"])
            },
            "webpage_db": {
                "name": self.current_webpage_db["name"],
                "health": self.db_manager._check_database_health(self.current_webpage_db["name"])
            }
        }

    def get_crawling_status(self) -> Dict:
        """Get current crawling status"""
        return {
            "active": True,
            "stats": self.stats,
            "current_databases": {
                "backlink": self.current_backlink_db["name"] if self.current_backlink_db else None,
                "webpage": self.current_webpage_db["name"] if self.current_webpage_db else None
            },
            "database_health": self.db_manager.get_all_database_status()
        }
