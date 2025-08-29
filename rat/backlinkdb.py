import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any

class BacklinkDatabase:
    def __init__(self, db_path="backlinks.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Backlinks table
        cursor.execute('''
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

    def store_backlinks(self, backlinks: List[Any]):
        """Store backlinks in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for backlink in backlinks:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO backlinks
                    (source_url, target_url, anchor_text, context, page_title,
                     domain_authority, is_nofollow)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
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

    def store_domain_scores(self, domain_scores: Dict[str, float]):
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

    def get_backlinks_for_url(self, target_url: str) -> List[Dict]:
        """Retrieve all backlinks for a specific URL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM backlinks WHERE target_url = ?
            ORDER BY crawl_date DESC
        ''', (target_url,))

        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results