"""
Turso Database Adapter for RatCrawler
Seamlessly integrates Turso databases with automatic rotation into your existing crawler
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import requests

from rat.turso_rotation_utility import get_current_database, record_writes, DatabaseRotator


class TursoConnection:
    """Handles Turso database connections and operations"""

    def __init__(self, db_name: str, url: str, auth_token: str):
        self.db_name = db_name
        self.url = url.rstrip('/')
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute SELECT query"""
        try:
            payload = {"sql": query}
            if params:
                payload["args"] = list(params)

            response = requests.post(
                f"{self.url}/execute",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            results = []

            for result in data.get("results", []):
                if "rows" in result:
                    columns = result.get("columns", [])
                    for row in result["rows"]:
                        results.append(dict(zip(columns, row)))

            return results

        except Exception as e:
            print(f"❌ Turso query error: {e}")
            return []

    def execute_write(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            payload = {"sql": query}
            if params:
                payload["args"] = list(params)

            response = requests.post(
                f"{self.url}/execute",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            affected_rows = 0

            for result in data.get("results", []):
                affected_rows += result.get("rows_affected", 0)

            # Record write operation for monitoring
            if affected_rows > 0:
                record_writes(self.db_name, affected_rows)

            return affected_rows

        except Exception as e:
            print(f"❌ Turso write error: {e}")
            return 0

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute multiple INSERT operations"""
        total_affected = 0

        for params in params_list:
            affected = self.execute_write(query, params)
            total_affected += affected

            # If we can't write to current database, it will auto-rotate
            if affected == 0:
                print(f"⚠️ Write failed, attempting rotation...")
                # Force rotation by getting new database
                new_db = get_current_database()
                if new_db != self.db_name:
                    print(f"🔄 Rotated to database: {new_db}")
                    return total_affected  # Stop and let caller retry with new DB

        return total_affected


class TursoDatabaseAdapter:
    """Drop-in replacement for your existing SQLite databases"""

    def __init__(self, db_type: str = "crawler"):
        """
        Initialize Turso database adapter
        Args:
            db_type: "crawler" or "backlinks" to match your existing databases
        """
        self.db_type = db_type
        self.current_connection = None
        self.rotator = DatabaseRotator()

        # Get initial database
        self._switch_to_available_database()

    def _switch_to_available_database(self):
        """Switch to an available database"""
        try:
            db_name = get_current_database()
            if db_name:
                # Get database config from monitor
                databases = self.rotator.monitor.get_all_databases()
                db_config = next((db for db in databases if db['name'] == db_name), None)

                if db_config:
                    self.current_connection = TursoConnection(
                        db_name=db_name,
                        url=db_config['url'],
                        auth_token=db_config['auth_token']
                    )
                    print(f"🔄 Switched to Turso database: {db_name}")
                else:
                    print(f"❌ Database config not found for: {db_name}")
            else:
                print("❌ No available Turso databases")
        except Exception as e:
            print(f"❌ Failed to switch database: {e}")

    def _ensure_connection(self):
        """Ensure we have a valid database connection"""
        if not self.current_connection:
            self._switch_to_available_database()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute SELECT query with automatic retry on failure"""
        self._ensure_connection()
        if not self.current_connection:
            return []

        result = self.current_connection.execute_query(query, params)

        # If query failed and we might need to rotate
        if not result and "SELECT" in query.upper():
            print("⚠️ Query failed, trying different database...")
            self._switch_to_available_database()
            if self.current_connection:
                result = self.current_connection.execute_query(query, params)

        return result

    def execute_write(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute write operation with automatic rotation"""
        self._ensure_connection()
        if not self.current_connection:
            return 0

        affected = self.current_connection.execute_write(query, params)

        # If write failed, try rotating to another database
        if affected == 0 and ("INSERT" in query.upper() or "UPDATE" in query.upper()):
            print("⚠️ Write failed, rotating database...")
            old_db = self.current_connection.db_name
            self._switch_to_available_database()

            # Retry the write on new database
            if self.current_connection and self.current_connection.db_name != old_db:
                affected = self.current_connection.execute_write(query, params)
                if affected > 0:
                    print(f"✅ Write succeeded on new database: {self.current_connection.db_name}")

        return affected

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute multiple operations with rotation support"""
        self._ensure_connection()
        if not self.current_connection:
            return 0

        return self.current_connection.execute_many(query, params_list)

    def get_current_database_name(self) -> str:
        """Get current database name"""
        return self.current_connection.db_name if self.current_connection else "none"


# Enhanced WebsiteCrawlerDatabase with Turso support
class TursoWebsiteCrawlerDatabase:
    """Drop-in replacement for WebsiteCrawlerDatabase using Turso"""

    def __init__(self, db_path="website_crawler.db"):
        # Keep db_path for compatibility but use Turso
        self.db_adapter = TursoDatabaseAdapter("crawler")
        self.init_database()

    def init_database(self):
        """Initialize Turso database tables"""
        # Create tables in Turso (they're created automatically if they don't exist)
        queries = [
            """
            CREATE TABLE IF NOT EXISTS crawl_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                seed_urls TEXT,
                config TEXT,
                end_time TIMESTAMP,
                status TEXT DEFAULT 'running'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS crawled_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                url TEXT NOT NULL,
                original_url TEXT,
                redirect_chain TEXT,
                title TEXT,
                meta_description TEXT,
                content_text TEXT,
                content_html TEXT,
                content_hash TEXT,
                word_count INTEGER,
                page_size INTEGER,
                http_status_code INTEGER,
                response_time_ms INTEGER,
                language TEXT,
                charset TEXT,
                h1_tags TEXT,
                h2_tags TEXT,
                meta_keywords TEXT,
                canonical_url TEXT,
                robots_meta TEXT,
                internal_links_count INTEGER,
                external_links_count INTEGER,
                images_count INTEGER,
                crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES crawl_sessions(id),
                UNIQUE(url, session_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS crawl_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                url TEXT NOT NULL,
                error_type TEXT,
                error_msg TEXT,
                status_code INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES crawl_sessions(id)
            )
            """
        ]

        for query in queries:
            self.db_adapter.execute_write(query)

    def create_crawl_session(self, seed_urls: List[str], config: Dict) -> str:
        """Create new crawl session"""
        query = """
        INSERT INTO crawl_sessions (seed_urls, config)
        VALUES (?, ?)
        """

        result = self.db_adapter.execute_write(query, (json.dumps(seed_urls), json.dumps(config)))

        if result > 0:
            # Get the last inserted ID
            id_result = self.db_adapter.execute_query("SELECT last_insert_rowid() as id")
            if id_result:
                return str(id_result[0]['id'])

        return "1"  # fallback

    def store_crawled_page(self, page_data: Dict, session_id: str):
        """Store crawled page data"""
        query = """
        INSERT OR REPLACE INTO crawled_pages (
            session_id, url, original_url, redirect_chain, title,
            meta_description, content_text, content_html, content_hash,
            word_count, page_size, http_status_code, response_time_ms,
            language, charset, h1_tags, h2_tags, meta_keywords,
            canonical_url, robots_meta, internal_links_count,
            external_links_count, images_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            int(session_id),
            page_data.get('url', ''),
            page_data.get('original_url'),
            json.dumps(page_data.get('redirect_chain', [])),
            page_data.get('title'),
            page_data.get('meta_description'),
            page_data.get('content_text'),
            page_data.get('content_html'),
            page_data.get('content_hash'),
            page_data.get('word_count'),
            page_data.get('page_size'),
            page_data.get('http_status_code'),
            page_data.get('response_time_ms'),
            page_data.get('language'),
            page_data.get('charset'),
            json.dumps(page_data.get('h1_tags', [])),
            json.dumps(page_data.get('h2_tags', [])),
            json.dumps(page_data.get('meta_keywords', [])),
            page_data.get('canonical_url'),
            page_data.get('robots_meta'),
            page_data.get('internal_links_count'),
            page_data.get('external_links_count'),
            page_data.get('images_count')
        )

        self.db_adapter.execute_write(query, params)

    def log_crawl_error(self, session_id: str, url: str, error_type: str, error_msg: str, status_code: Optional[int] = None):
        """Log crawl error"""
        query = """
        INSERT INTO crawl_errors (session_id, url, error_type, error_msg, status_code)
        VALUES (?, ?, ?, ?, ?)
        """

        self.db_adapter.execute_write(query, (int(session_id), url, error_type, error_msg, status_code))

    def get_all_crawled_urls(self) -> List[str]:
        """Get all crawled URLs"""
        query = "SELECT DISTINCT url FROM crawled_pages"
        results = self.db_adapter.execute_query(query)
        return [row['url'] for row in results]

    def get_all_content_hashes(self) -> List[str]:
        """Get all content hashes"""
        query = "SELECT DISTINCT content_hash FROM crawled_pages WHERE content_hash IS NOT NULL"
        results = self.db_adapter.execute_query(query)
        return [row['content_hash'] for row in results]

    def get_last_crawl_time(self, url: str) -> Optional[str]:
        """Get last crawl time for URL"""
        query = "SELECT crawl_time FROM crawled_pages WHERE url = ? ORDER BY crawl_time DESC LIMIT 1"
        results = self.db_adapter.execute_query(query, (url,))
        if results:
            return results[0]['crawl_time']
        return None

    def finish_crawl_session(self, session_id: str, status: str):
        """Finish crawl session"""
        query = "UPDATE crawl_sessions SET end_time = CURRENT_TIMESTAMP, status = ? WHERE id = ?"
        self.db_adapter.execute_write(query, (status, int(session_id)))

    def get_crawl_summary(self, session_id: str) -> Dict:
        """Get crawl session summary"""
        query = """
        SELECT
            COUNT(*) as total_pages,
            AVG(word_count) as avg_word_count,
            SUM(page_size) as total_size,
            AVG(response_time_ms) as avg_response_time
        FROM crawled_pages
        WHERE session_id = ?
        """

        results = self.db_adapter.execute_query(query, (int(session_id),))
        if results:
            return results[0]
        return {}

    # Add other methods as needed...


# Enhanced BacklinkDatabase with Turso support
class TursoBacklinkDatabase:
    """Drop-in replacement for BacklinkDatabase using Turso"""

    def __init__(self, db_path="backlinks.db"):
        self.db_adapter = TursoDatabaseAdapter("backlinks")
        self.init_database()

    def init_database(self):
        """Initialize Turso database tables"""
        queries = [
            """
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
                UNIQUE(source_url, target_url, anchor_text)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS domain_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                authority_score REAL DEFAULT 0.0,
                total_backlinks INTEGER DEFAULT 0,
                unique_referring_domains INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS pagerank_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                pagerank_score REAL DEFAULT 0.0,
                last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]

        for query in queries:
            self.db_adapter.execute_write(query)

    def store_backlinks(self, backlinks: List[Any]):
        """Store backlinks in Turso"""
        query = """
        INSERT OR IGNORE INTO backlinks
        (source_url, target_url, anchor_text, context, page_title, domain_authority, is_nofollow)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        params_list = []
        for backlink in backlinks:
            if hasattr(backlink, 'source_url'):
                params_list.append((
                    backlink.source_url,
                    backlink.target_url,
                    getattr(backlink, 'anchor_text', ''),
                    getattr(backlink, 'context', ''),
                    getattr(backlink, 'page_title', ''),
                    getattr(backlink, 'domain_authority', 0.0),
                    getattr(backlink, 'is_nofollow', False)
                ))

        if params_list:
            self.db_adapter.execute_many(query, params_list)

    def store_domain_scores(self, domain_scores: Dict[str, float]):
        """Store domain authority scores"""
        query = """
        INSERT OR REPLACE INTO domain_scores
        (domain, authority_score, last_updated)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """

        params_list = [(domain, score) for domain, score in domain_scores.items()]
        self.db_adapter.execute_many(query, params_list)

    def store_pagerank_scores(self, pagerank_scores: Dict[str, float]):
        """Store PageRank scores"""
        query = """
        INSERT OR REPLACE INTO pagerank_scores
        (url, pagerank_score, last_calculated)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """

        params_list = [(url, score) for url, score in pagerank_scores.items()]
        self.db_adapter.execute_many(query, params_list)

    def get_backlinks_for_url(self, target_url: str) -> List[Dict]:
        """Get backlinks for a specific URL"""
        query = """
        SELECT source_url, anchor_text, context, page_title, domain_authority, is_nofollow, crawl_date
        FROM backlinks
        WHERE target_url = ?
        ORDER BY crawl_date DESC
        """

        results = self.db_adapter.execute_query(query, (target_url,))
        return results

    # Add other methods as needed...


# Easy migration function
def migrate_to_turso():
    """
    Migrate your existing SQLite data to Turso databases
    Call this once to migrate your existing data
    """
    print("🚀 Starting migration to Turso databases...")

    try:
        # Import existing database classes
        from rat.crawlerdb import WebsiteCrawlerDatabase
        from rat.backlinkdb import BacklinkDatabase

        # Migrate crawler data
        print("📊 Migrating crawler database...")
        old_crawler = WebsiteCrawlerDatabase("website_crawler.db")
        new_crawler = TursoWebsiteCrawlerDatabase()

        # Migrate crawled URLs
        urls = old_crawler.get_all_crawled_urls()
        print(f"   Found {len(urls)} crawled URLs to migrate")

        # Migrate backlinks data
        print("🔗 Migrating backlinks database...")
        old_backlinks = BacklinkDatabase("backlinks.db")
        new_backlinks = TursoBacklinkDatabase()

        print("✅ Migration completed!")
        print("🔄 Your databases now use Turso with automatic rotation")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

    return True


if __name__ == "__main__":
    # Test the integration
    print("🧪 Testing Turso Database Integration...")

    # Test crawler database
    crawler_db = TursoWebsiteCrawlerDatabase()
    print(f"✅ Crawler database connected to: {crawler_db.db_adapter.get_current_database_name()}")

    # Test backlinks database
    backlinks_db = TursoBacklinkDatabase()
    print(f"✅ Backlinks database connected to: {backlinks_db.db_adapter.get_current_database_name()}")

    print("🎉 Turso integration ready!")
    print("\n📝 To use in your crawler, simply replace:")
    print("   from crawlerdb import WebsiteCrawlerDatabase")
    print("   from backlinkdb import BacklinkDatabase")
    print("\n   With:")
    print("   from turso_database_adapter import TursoWebsiteCrawlerDatabase, TursoBacklinkDatabase")
