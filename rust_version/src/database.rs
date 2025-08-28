use rusqlite::{Connection, Result, params, OptionalExtension};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use crate::models::*;
use serde_json;

#[derive(Debug)]
pub struct WebsiteCrawlerDatabase {
    conn: Connection,
}

impl WebsiteCrawlerDatabase {
    pub fn new(db_path: &str) -> Result<Self> {
        let conn = Connection::open(db_path)?;
        let mut db = Self { conn };
        db.init_database()?;
        Ok(db)
    }

    fn init_database(&mut self) -> Result<()> {
        // Crawl sessions table
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS crawl_sessions (
                id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                seed_urls TEXT NOT NULL,
                config TEXT NOT NULL,
                end_time TEXT,
                status TEXT DEFAULT 'running'
            )",
            [],
        )?;

        // Crawled pages table
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS crawled_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
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
                crawl_time TEXT,
                FOREIGN KEY(session_id) REFERENCES crawl_sessions(id)
            )",
            [],
        )?;

        // Crawl errors table
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS crawl_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                url TEXT NOT NULL,
                error_type TEXT,
                error_msg TEXT,
                status_code INTEGER,
                timestamp TEXT,
                FOREIGN KEY(session_id) REFERENCES crawl_sessions(id)
            )",
            [],
        )?;

        Ok(())
    }

    pub fn create_crawl_session(&mut self, seed_urls: &[String], config: &serde_json::Value) -> Result<String> {
        let session = CrawlSession::new(seed_urls.to_vec(), config.clone());
        let seed_urls_json = serde_json::to_string(&session.seed_urls)
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(e.into()))?;
        let config_json = serde_json::to_string(&session.config)
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(e.into()))?;

        self.conn.execute(
            "INSERT INTO crawl_sessions (id, start_time, seed_urls, config, status)
             VALUES (?, ?, ?, ?, ?)",
            params![
                session.id,
                session.start_time.to_rfc3339(),
                seed_urls_json,
                config_json,
                session.status
            ],
        )?;

        Ok(session.id)
    }

    pub fn store_crawled_page(&mut self, page: &CrawledPage, session_id: &str) -> Result<()> {
        let redirect_chain_json = serde_json::to_string(&page.redirect_chain)
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(e.into()))?;
        let h1_tags_json = serde_json::to_string(&page.h1_tags)
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(e.into()))?;
        let h2_tags_json = serde_json::to_string(&page.h2_tags)
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(e.into()))?;

        self.conn.execute(
            "INSERT INTO crawled_pages
             (session_id, url, original_url, redirect_chain, title, meta_description,
              content_text, content_html, content_hash, word_count, page_size,
              http_status_code, response_time_ms, language, charset, h1_tags,
              h2_tags, meta_keywords, canonical_url, robots_meta, internal_links_count,
              external_links_count, images_count, crawl_time)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            params![
                session_id,
                &page.url,
                &page.original_url,
                redirect_chain_json,
                &page.title,
                &page.meta_description,
                &page.content_text,
                &page.content_html,
                &page.content_hash,
                page.word_count as i64,
                page.page_size as i64,
                page.http_status_code as i64,
                page.response_time_ms as i64,
                &page.language,
                &page.charset,
                h1_tags_json,
                h2_tags_json,
                &page.meta_keywords,
                &page.canonical_url,
                &page.robots_meta,
                page.internal_links_count as i64,
                page.external_links_count as i64,
                page.images_count as i64,
                page.crawl_time.to_rfc3339()
            ],
        )?;

        Ok(())
    }

    pub fn log_crawl_error(&mut self, session_id: &str, url: &str, error_type: &str, error_msg: &str, status_code: Option<u16>) -> Result<()> {
        self.conn.execute(
            "INSERT INTO crawl_errors (session_id, url, error_type, error_msg, status_code, timestamp)
             VALUES (?, ?, ?, ?, ?, ?)",
            params![
                session_id,
                url,
                error_type,
                error_msg,
                status_code.map(|c| c as i64),
                Utc::now().to_rfc3339()
            ],
        )?;

        Ok(())
    }

    pub fn get_all_crawled_urls(&self) -> Result<Vec<String>> {
        let mut stmt = self.conn.prepare("SELECT DISTINCT url FROM crawled_pages")?;
        let urls = stmt.query_map([], |row| row.get(0))?
            .collect::<Result<Vec<String>>>()?;
        Ok(urls)
    }

    pub fn get_all_content_hashes(&self) -> Result<Vec<String>> {
        let mut stmt = self.conn.prepare("SELECT DISTINCT content_hash FROM crawled_pages")?;
        let hashes = stmt.query_map([], |row| row.get(0))?
            .collect::<Result<Vec<String>>>()?;
        Ok(hashes)
    }

    pub fn get_last_crawl_time(&self, url: &str) -> Result<Option<String>> {
        let mut stmt = self.conn.prepare(
            "SELECT MAX(crawl_time) FROM crawled_pages WHERE url = ?"
        )?;
        let result = stmt.query_row(params![url], |row| row.get(0)).optional()?;
        Ok(result)
    }

    pub fn finish_crawl_session(&mut self, session_id: &str, status: &str) -> Result<()> {
        self.conn.execute(
            "UPDATE crawl_sessions SET end_time = ?, status = ? WHERE id = ?",
            params![Utc::now().to_rfc3339(), status, session_id],
        )?;
        Ok(())
    }

    pub fn get_crawl_summary(&self, session_id: &str) -> Result<HashMap<String, usize>> {
        let pages_crawled: usize = self.conn.query_row(
            "SELECT COUNT(*) FROM crawled_pages WHERE session_id = ?",
            params![session_id],
            |row| row.get(0),
        )?;

        let errors: usize = self.conn.query_row(
            "SELECT COUNT(*) FROM crawl_errors WHERE session_id = ?",
            params![session_id],
            |row| row.get(0),
        )?;

        let mut summary = HashMap::new();
        summary.insert("pages_crawled".to_string(), pages_crawled);
        summary.insert("errors".to_string(), errors);

        Ok(summary)
    }
}

#[derive(Debug)]
pub struct BacklinkDatabase {
    conn: Connection,
}

impl BacklinkDatabase {
    pub fn new(db_path: &str) -> Result<Self> {
        let conn = Connection::open(db_path)?;
        let mut db = Self { conn };
        db.init_database()?;
        Ok(db)
    }

    fn init_database(&mut self) -> Result<()> {
        // Backlinks table
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS backlinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                target_url TEXT NOT NULL,
                anchor_text TEXT,
                context TEXT,
                page_title TEXT,
                domain_authority REAL DEFAULT 0.0,
                is_nofollow BOOLEAN DEFAULT FALSE,
                crawl_date TEXT,
                UNIQUE(source_url, target_url, anchor_text)
            )",
            [],
        )?;

        // Domain scores table
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS domain_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                authority_score REAL DEFAULT 0.0,
                total_backlinks INTEGER DEFAULT 0,
                unique_referring_domains INTEGER DEFAULT 0,
                last_updated TEXT
            )",
            [],
        )?;

        // PageRank scores table
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS pagerank_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                pagerank_score REAL DEFAULT 0.0,
                last_calculated TEXT
            )",
            [],
        )?;

        Ok(())
    }

    pub fn store_backlinks(&mut self, backlinks: &[BacklinkData]) -> Result<()> {
        for backlink in backlinks {
            self.conn.execute(
                "INSERT OR REPLACE INTO backlinks
                 (source_url, target_url, anchor_text, context, page_title,
                  domain_authority, is_nofollow, crawl_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                params![
                    &backlink.source_url,
                    &backlink.target_url,
                    &backlink.anchor_text,
                    &backlink.context,
                    &backlink.page_title,
                    backlink.domain_authority,
                    backlink.is_nofollow,
                    backlink.crawl_date.to_rfc3339()
                ],
            )?;
        }
        Ok(())
    }

    pub fn get_backlinks_for_url(&self, target_url: &str) -> Result<Vec<BacklinkData>> {
        let mut stmt = self.conn.prepare(
            "SELECT source_url, target_url, anchor_text, context, page_title,
                    domain_authority, is_nofollow, crawl_date
             FROM backlinks WHERE target_url = ? ORDER BY crawl_date DESC"
        )?;

        let backlinks = stmt.query_map(params![target_url], |row| {
            Ok(BacklinkData {
                source_url: row.get(0)?,
                target_url: row.get(1)?,
                anchor_text: row.get(2)?,
                context: row.get(3)?,
                page_title: row.get(4)?,
                domain_authority: row.get(5)?,
                is_nofollow: row.get(6)?,
                crawl_date: DateTime::parse_from_rfc3339(&row.get::<_, String>(7)?)
                    .unwrap_or_else(|_| Utc::now().into())
                    .with_timezone(&Utc),
            })
        })?
        .collect::<Result<Vec<_>>>()?;

        Ok(backlinks)
    }

    pub fn store_domain_scores(&mut self, domain_scores: &HashMap<String, f64>) -> Result<()> {
        for (domain, score) in domain_scores {
            self.conn.execute(
                "INSERT OR REPLACE INTO domain_scores (domain, authority_score, last_updated)
                 VALUES (?, ?, ?)",
                params![domain, score, Utc::now().to_rfc3339()],
            )?;
        }
        Ok(())
    }

    pub fn store_pagerank_scores(&mut self, pagerank_scores: &HashMap<String, f64>) -> Result<()> {
        for (url, score) in pagerank_scores {
            self.conn.execute(
                "INSERT OR REPLACE INTO pagerank_scores (url, pagerank_score, last_calculated)
                 VALUES (?, ?, ?)",
                params![url, score, Utc::now().to_rfc3339()],
            )?;
        }
        Ok(())
    }
}
