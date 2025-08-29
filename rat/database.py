"""
Turso Database Integration for RatCrawler
Uses libSQL (SQLite-compatible) with Turso's distributed database service.
"""

from rat.config import config
from libsql_client import Client
import json
from typing import List, Dict, Any, Optional, Union
import sqlite3
from datetime import datetime


class TursoDatabase:
    """
    Turso database client using libSQL.
    Provides MongoDB-like interface but with SQLite/Turso backend.
    """

    def __init__(self, db_name: str = "webcrawler_db"):
        """Initialize Turso database connection"""
        self.db_name = db_name

        # Initialize Turso client
        if config.TURSO_URL and config.TURSO_AUTH_TOKEN:
            # Remote Turso database
            self.client = Client(
                url=config.TURSO_URL,
                auth_token=config.TURSO_AUTH_TOKEN
            )
            self.is_remote = True
        else:
            # Local SQLite fallback
            print("⚠️  Turso credentials not found, using local SQLite")
            self.client = None
            self.local_db_path = f"{db_name}.db"
            self.is_remote = False

        # Initialize database schema
        self._init_schema()

    def _init_schema(self):
        """Initialize database tables and schema"""
        schema_sql = """
        -- Main web data collection
        CREATE TABLE IF NOT EXISTS webdata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT,
            content TEXT,
            metadata TEXT,  -- JSON field for additional data
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Crawled pages with full details
        CREATE TABLE IF NOT EXISTS crawled_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT,
            content TEXT,
            meta_description TEXT,
            word_count INTEGER,
            http_status INTEGER,
            response_time_ms INTEGER,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Domain authority tracking
        CREATE TABLE IF NOT EXISTS domain_authority (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            authority_score REAL DEFAULT 0.0,
            backlinks_count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Backlinks data
        CREATE TABLE IF NOT EXISTS backlinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL,
            target_url TEXT NOT NULL,
            anchor_text TEXT,
            link_type TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_url, target_url)
        );

        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_webdata_url ON webdata(url);
        CREATE INDEX IF NOT EXISTS idx_crawled_pages_url ON crawled_pages(url);
        CREATE INDEX IF NOT EXISTS idx_domain_authority_domain ON domain_authority(domain);
        CREATE INDEX IF NOT EXISTS idx_backlinks_target ON backlinks(target_url);
        """

        if self.is_remote:
            # Execute schema on remote Turso
            try:
                self.client.execute(schema_sql)
            except Exception as e:
                print(f"Schema initialization error: {e}")
        else:
            # Execute schema on local SQLite
            with sqlite3.connect(self.local_db_path) as conn:
                conn.executescript(schema_sql)

    def _execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts"""
        if self.is_remote:
            try:
                result = self.client.execute(query, params or [])
                # Convert result to list of dicts
                if result.rows:
                    columns = [col.name for col in result.columns]
                    return [dict(zip(columns, row)) for row in result.rows]
                return []
            except Exception as e:
                print(f"Turso query error: {e}")
                return []
        else:
            with sqlite3.connect(self.local_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]

    def _execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        if self.is_remote:
            try:
                result = self.client.execute(query, params or [])
                return result.rows_affected or 0
            except Exception as e:
                print(f"Turso update error: {e}")
                return 0
        else:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.rowcount

    def get_collection(self, collection_name: str):
        """Return a collection-like object for the specified table"""
        return TursoCollection(self, collection_name)

    def insert_document(self, document: Union[Dict, List[Dict]], collection_name: str = "webdata") -> Union[str, List[str]]:
        """Insert a document or list of documents into the specified collection/table."""
        if isinstance(document, list):
            if len(document) == 0:
                return []
            return self._insert_many_documents(document, collection_name)
        else:
            return self._insert_single_document(document, collection_name)

    def _insert_single_document(self, document: Dict, collection_name: str) -> str:
        """Insert a single document"""
        if collection_name == "webdata":
            # Handle webdata collection
            query = """
            INSERT INTO webdata (url, title, content, metadata)
            VALUES (?, ?, ?, ?)
            """
            metadata = json.dumps({k: v for k, v in document.items()
                                 if k not in ['url', 'title', 'content']})

            result = self._execute_update(query, (
                document.get('url', ''),
                document.get('title', ''),
                document.get('content', ''),
                metadata
            ))

            if result > 0:
                # Get the last inserted ID
                if self.is_remote:
                    # For Turso, we might need to handle this differently
                    return f"doc_{datetime.now().timestamp()}"
                else:
                    with sqlite3.connect(self.local_db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT last_insert_rowid()")
                        return str(cursor.fetchone()[0])
            return ""

        elif collection_name == "crawled_pages":
            # Handle crawled_pages collection
            query = """
            INSERT OR REPLACE INTO crawled_pages
            (url, title, content, meta_description, word_count, http_status, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            self._execute_update(query, (
                document.get('url', ''),
                document.get('title', ''),
                document.get('content', ''),
                document.get('meta_description', ''),
                document.get('word_count', 0),
                document.get('http_status', 200),
                document.get('response_time_ms', 0)
            ))
            return f"crawled_{datetime.now().timestamp()}"

        else:
            # Generic insert for other collections
            columns = ', '.join(document.keys())
            placeholders = ', '.join(['?'] * len(document))
            query = f"INSERT INTO {collection_name} ({columns}) VALUES ({placeholders})"

            self._execute_update(query, tuple(document.values()))
            return f"{collection_name}_{datetime.now().timestamp()}"

    def _insert_many_documents(self, documents: List[Dict], collection_name: str) -> List[str]:
        """Insert multiple documents efficiently"""
        inserted_ids = []

        if collection_name == "webdata":
            query = """
            INSERT INTO webdata (url, title, content, metadata)
            VALUES (?, ?, ?, ?)
            """

            values = []
            for doc in documents:
                metadata = json.dumps({k: v for k, v in doc.items()
                                     if k not in ['url', 'title', 'content']})
                values.append((
                    doc.get('url', ''),
                    doc.get('title', ''),
                    doc.get('content', ''),
                    metadata
                ))

            if self.is_remote:
                # For Turso, execute multiple statements
                for value in values:
                    try:
                        self.client.execute(query, value)
                        inserted_ids.append(f"doc_{datetime.now().timestamp()}")
                    except Exception as e:
                        print(f"Insert error: {e}")
            else:
                with sqlite3.connect(self.local_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.executemany(query, values)
                    conn.commit()
                    # Generate IDs for successful inserts
                    inserted_ids = [f"doc_{i}" for i in range(len(documents))]

        return inserted_ids

    def find_documents(self, collection_name: str, query: Dict = None, limit: int = 100) -> List[Dict]:
        """Find documents in a collection with optional query"""
        if query is None:
            query_sql = f"SELECT * FROM {collection_name} LIMIT {limit}"
            return self._execute_query(query_sql)
        else:
            # Simple query building - can be enhanced for complex queries
            where_clause = " AND ".join([f"{k} = ?" for k in query.keys()])
            query_sql = f"SELECT * FROM {collection_name} WHERE {where_clause} LIMIT {limit}"
            return self._execute_query(query_sql, tuple(query.values()))

    def get_domain_authority_scores(self) -> Dict[str, float]:
        """Get domain authority scores (for compatibility with existing code)"""
        results = self._execute_query("SELECT domain, authority_score FROM domain_authority")
        return {row['domain']: row['authority_score'] for row in results}

    def close(self):
        """Close database connection"""
        if not self.is_remote and hasattr(self, 'local_db_path'):
            # Local SQLite doesn't need explicit closing
            pass
        # Turso client doesn't need explicit closing


class TursoCollection:
    """Collection-like interface for Turso tables"""

    def __init__(self, database: TursoDatabase, collection_name: str):
        self.database = database
        self.collection_name = collection_name

    def insert_one(self, document: Dict) -> str:
        """Insert a single document"""
        return self.database._insert_single_document(document, self.collection_name)

    def insert_many(self, documents: List[Dict]) -> List[str]:
        """Insert multiple documents"""
        return self.database._insert_many_documents(documents, self.collection_name)

    def find(self, query: Dict = None, limit: int = 100) -> List[Dict]:
        """Find documents with optional query"""
        return self.database.find_documents(self.collection_name, query, limit)

    def find_one(self, query: Dict = None) -> Optional[Dict]:
        """Find a single document"""
        results = self.find(query, limit=1)
        return results[0] if results else None


# Backward compatibility - alias for existing code
Database = TursoDatabase


# Example usage and testing
if __name__ == "__main__":
    # Initialize database
    db = TursoDatabase()

    # Insert a test document
    test_doc = {
        "url": "https://example.com",
        "title": "Example Page",
        "content": "This is test content",
        "word_count": 150,
        "http_status": 200
    }

    # Insert into different collections
    webdata_id = db.insert_document(test_doc, "webdata")
    crawled_id = db.insert_document(test_doc, "crawled_pages")

    print(f"Inserted webdata: {webdata_id}")
    print(f"Inserted crawled page: {crawled_id}")

    # Query data
    webdata = db.find_documents("webdata", limit=5)
    crawled_pages = db.find_documents("crawled_pages", limit=5)

    print(f"Webdata count: {len(webdata)}")
    print(f"Crawled pages count: {len(crawled_pages)}")

    # Test collection interface
    collection = db.get_collection("webdata")
    docs = collection.find(limit=3)
    print(f"Collection find: {len(docs)} documents")

    db.close()
