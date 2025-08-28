# website_crawler_db.py
import sqlite3
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
from backlinkprocessor import BacklinkData

class WebsiteCrawlerDatabase:
    def __init__(self, db_path="website_crawler.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Crawl sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                seed_urls TEXT,
                config TEXT,
                end_time TIMESTAMP,
                status TEXT DEFAULT 'running'
            )
        ''')

        # Crawled pages table
        cursor.execute('''
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
        ''')

        # Crawl errors table
        cursor.execute('''
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
        ''')

        # Backlinks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backlinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                source_url TEXT NOT NULL,
                target_url TEXT NOT NULL,
                anchor_text TEXT,
                context TEXT,
                page_title TEXT,
                domain_authority REAL DEFAULT 0.0,
                is_nofollow BOOLEAN DEFAULT FALSE,
                crawl_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES crawl_sessions(id),
                UNIQUE(source_url, target_url, anchor_text, session_id)
            )
        ''')

        # Domain scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS domain_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                authority_score REAL DEFAULT 0.0,
                total_backlinks INTEGER DEFAULT 0,
                unique_referring_domains INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # PageRank scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pagerank_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                pagerank_score REAL DEFAULT 0.0,
                last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def create_crawl_session(self, seed_urls: List[str], config: Dict) -> str:
        """Create a new crawl session and return its ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        seed_json = json.dumps(seed_urls)
        config_json = json.dumps(config)

        cursor.execute('''
            INSERT INTO crawl_sessions (seed_urls, config)
            VALUES (?, ?)
        ''', (seed_json, config_json))

        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return str(session_id)

    def store_crawled_page(self, page_data: Dict, session_id: str):
        """Store crawled page data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO crawled_pages
                (session_id, url, original_url, redirect_chain, title, meta_description,
                 content_text, content_html, content_hash, word_count, page_size,
                 http_status_code, response_time_ms, language, charset, h1_tags,
                 h2_tags, meta_keywords, canonical_url, robots_meta, internal_links_count,
                 external_links_count, images_count, crawl_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                page_data['url'],
                page_data['original_url'],
                json.dumps(page_data['redirect_chain']),
                page_data['title'],
                page_data['meta_description'],
                page_data['content_text'],
                page_data['content_html'],
                page_data['content_hash'],
                page_data['word_count'],
                page_data['page_size'],
                page_data['http_status_code'],
                page_data['response_time_ms'],
                page_data['language'],
                page_data['charset'],
                json.dumps(page_data['h1_tags']),
                json.dumps(page_data['h2_tags']),
                page_data['meta_keywords'],
                page_data['canonical_url'],
                page_data['robots_meta'],
                page_data['internal_links_count'],
                page_data['external_links_count'],
                page_data['images_count'],
                page_data['crawl_time']
            ))
        except sqlite3.Error as e:
            print(f"Error storing page: {e}")

        conn.commit()
        conn.close()

    def log_crawl_error(self, session_id: str, url: str, error_type: str, error_msg: str, status_code: Optional[int] = None):
        """Log a crawl error."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO crawl_errors (session_id, url, error_type, error_msg, status_code)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, url, error_type, error_msg, status_code))

        conn.commit()
        conn.close()

    def store_backlinks(self, backlinks: List[BacklinkData], session_id: str):
        """Store backlinks in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for backlink in backlinks:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO backlinks
                    (session_id, source_url, target_url, anchor_text, context, page_title,
                     domain_authority, is_nofollow)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    backlink.source_url,
                    backlink.target_url,
                    backlink.anchor_text,
                    backlink.context,
                    backlink.page_title,
                    backlink.domain_authority,
                    backlink.is_nofollow
                ))
            except sqlite3.Error as e:
                print(f"Error storing backlink: {e}")

        conn.commit()
        conn.close()

    def store_domain_stats(self, domain_scores: Dict[str, float]):
        """Store domain authority scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for domain, score in domain_scores.items():
            cursor.execute('''
                INSERT OR REPLACE INTO domain_scores (domain, authority_score)
                VALUES (?, ?)
            ''', (domain, score))

        conn.commit()
        conn.close()

    def store_pagerank_scores(self, pagerank_scores: Dict[str, float]):
        """Store PageRank scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for url, score in pagerank_scores.items():
            cursor.execute('''
                INSERT OR REPLACE INTO pagerank_scores (url, pagerank_score)
                VALUES (?, ?)
            ''', (url, score))

        conn.commit()
        conn.close()

    def finish_crawl_session(self, session_id: str, status: str):
        """Finish a crawl session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE crawl_sessions
            SET end_time = CURRENT_TIMESTAMP, status = ?
            WHERE id = ?
        ''', (status, session_id))

        conn.commit()
        conn.close()

    def get_crawl_summary(self, session_id: str) -> Dict:
        """Get summary of a crawl session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM crawled_pages WHERE session_id = ?
        ''', (session_id,))
        pages_crawled = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM backlinks WHERE session_id = ?
        ''', (session_id,))
        backlinks_found = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM crawl_errors WHERE session_id = ?
        ''', (session_id,))
        errors = cursor.fetchone()[0]

        conn.close()
        return {
            'pages_crawled': pages_crawled,
            'backlinks_found': backlinks_found,
            'errors': errors
        }

    def export_data(self, filename: str, format: str, table: str):
        """Export table data to CSV."""
        if format != 'csv':
            raise ValueError("Only CSV export supported")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'SELECT * FROM {table}')
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)

        conn.close()

    def get_all_crawled_urls(self) -> List[str]:
        """Get all unique crawled URLs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT DISTINCT url FROM crawled_pages')
        urls = [row[0] for row in cursor.fetchall()]

        conn.close()
        return urls

    def get_all_content_hashes(self) -> List[str]:
        """Get all unique content hashes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT DISTINCT content_hash FROM crawled_pages')
        hashes = [row[0] for row in cursor.fetchall()]

        conn.close()
        return hashes

    def get_last_crawl_time(self, url: str) -> Optional[str]:
        """Get the last crawl time for a URL."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT MAX(crawl_time) FROM crawled_pages WHERE url = ?
        ''', (url,))
        result = cursor.fetchone()[0]

        conn.close()
        return result

    def get_all_backlinks(self) -> List[Dict]:
        """Retrieve all backlinks from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM backlinks ORDER BY crawl_date DESC')
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results