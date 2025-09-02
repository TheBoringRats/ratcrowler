use crate::models::{BacklinkData, CrawlResult, SeedUrl, DashboardStats};
use anyhow::Result;
use chrono::{DateTime, Utc};
use rusqlite::{params, Connection, Row};
use std::path::Path;
use std::sync::{Arc, Mutex};
use log::{info, warn, error};

pub struct Database {
    conn: Arc<Mutex<Connection>>,
}

impl Database {
    pub fn new<P: AsRef<Path>>(db_path: P) -> Result<Self> {
        let conn = Connection::open(db_path)?;
        let db = Self {
            conn: Arc::new(Mutex::new(conn)),
        };
        db.init_tables()?;
        Ok(db)
    }

    fn init_tables(&self) -> Result<()> {
        let conn = self.conn.lock().unwrap();

        // Create backlinks table
        conn.execute(
            r#"
            CREATE TABLE IF NOT EXISTS backlinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                target_url TEXT NOT NULL,
                anchor_text TEXT,
                context TEXT,
                page_title TEXT,
                domain_authority REAL DEFAULT 0.0,
                is_nofollow BOOLEAN DEFAULT 0,
                discovered_at TEXT NOT NULL,
                UNIQUE(source_url, target_url)
            )
            "#,
            [],
        )?;

        // Create crawl_results table
        conn.execute(
            r#"
            CREATE TABLE IF NOT EXISTS crawl_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
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
                content_type TEXT,
                file_extension TEXT,
                crawl_success BOOLEAN DEFAULT 0,
                error_message TEXT,
                crawled_at TEXT NOT NULL
            )
            "#,
            [],
        )?;

        // Create seed_urls table
        conn.execute(
            r#"
            CREATE TABLE IF NOT EXISTS seed_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                added_at TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                last_crawled TEXT,
                crawl_count INTEGER DEFAULT 0
            )
            "#,
            [],
        )?;

        // Create stats table for dashboard
        conn.execute(
            r#"
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY,
                total_urls_crawled INTEGER DEFAULT 0,
                total_backlinks_found INTEGER DEFAULT 0,
                unique_domains INTEGER DEFAULT 0,
                crawl_rate_per_hour REAL DEFAULT 0.0,
                backlink_rate_per_hour REAL DEFAULT 0.0,
                database_size_mb REAL DEFAULT 0.0,
                system_memory_usage REAL DEFAULT 0.0,
                system_cpu_usage REAL DEFAULT 0.0,
                last_updated TEXT NOT NULL,
                current_mode TEXT DEFAULT 'idle',
                next_mode_switch TEXT
            )
            "#,
            [],
        )?;

        // Insert initial stats row if it doesn't exist
        conn.execute(
            "INSERT OR IGNORE INTO stats (id, last_updated) VALUES (1, ?)",
            params![Utc::now().to_rfc3339()],
        )?;

        // Create indexes for better performance
        let indexes = [
            "CREATE INDEX IF NOT EXISTS idx_backlinks_source ON backlinks(source_url)",
            "CREATE INDEX IF NOT EXISTS idx_backlinks_target ON backlinks(target_url)",
            "CREATE INDEX IF NOT EXISTS idx_crawl_results_url ON crawl_results(url)",
            "CREATE INDEX IF NOT EXISTS idx_crawl_results_crawled_at ON crawl_results(crawled_at)",
            "CREATE INDEX IF NOT EXISTS idx_seed_urls_priority ON seed_urls(priority DESC)",
        ];

        for index_sql in &indexes {
            conn.execute(index_sql, [])?;
        }

        info!("Database tables initialized successfully");
        Ok(())
    }

    pub async fn save_backlinks(&self, backlinks: &[BacklinkData]) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            r#"
            INSERT OR REPLACE INTO backlinks
            (source_url, target_url, anchor_text, context, page_title, domain_authority, is_nofollow, discovered_at)
            VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
            "#,
        )?;

        for backlink in backlinks {
            stmt.execute(params![
                backlink.source_url,
                backlink.target_url,
                backlink.anchor_text,
                backlink.context,
                backlink.page_title,
                backlink.domain_authority,
                backlink.is_nofollow,
                backlink.discovered_at.to_rfc3339(),
            ])?;
        }

        info!("Saved {} backlinks to database", backlinks.len());
        Ok(())
    }

    pub async fn save_crawl_result(&self, result: &CrawlResult) -> Result<()> {
        let conn = self.conn.lock().unwrap();

        conn.execute(
            r#"
            INSERT OR REPLACE INTO crawl_results
            (url, original_url, redirect_chain, title, meta_description, content_text, content_html,
             content_hash, word_count, page_size, http_status_code, response_time_ms, language,
             charset, h1_tags, h2_tags, meta_keywords, canonical_url, robots_meta,
             internal_links_count, external_links_count, images_count, content_type,
             file_extension, crawl_success, error_message, crawled_at)
            VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?18, ?19, ?20, ?21, ?22, ?23, ?24, ?25, ?26, ?27)
            "#,
            params![
                result.url,
                result.original_url,
                result.redirect_chain.as_ref().map(|v| serde_json::to_string(v).unwrap_or_default()),
                result.title,
                result.meta_description,
                result.content_text,
                result.content_html,
                result.content_hash,
                result.word_count,
                result.page_size,
                result.http_status_code,
                result.response_time_ms,
                result.language,
                result.charset,
                result.h1_tags.as_ref().map(|v| serde_json::to_string(v).unwrap_or_default()),
                result.h2_tags.as_ref().map(|v| serde_json::to_string(v).unwrap_or_default()),
                result.meta_keywords.as_ref().map(|v| serde_json::to_string(v).unwrap_or_default()),
                result.canonical_url,
                result.robots_meta,
                result.internal_links_count,
                result.external_links_count,
                result.images_count,
                result.content_type,
                result.file_extension,
                result.crawl_success,
                result.error_message,
                result.crawled_at.to_rfc3339(),
            ],
        )?;

        Ok(())
    }

    pub async fn get_seed_urls(&self, limit: i32) -> Result<Vec<SeedUrl>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT url, added_at, priority, last_crawled, crawl_count
             FROM seed_urls
             ORDER BY priority DESC, last_crawled ASC NULLS FIRST
             LIMIT ?",
        )?;

        let seed_iter = stmt.query_map(params![limit], |row| {
            Ok(SeedUrl {
                url: row.get(0)?,
                added_at: DateTime::parse_from_rfc3339(&row.get::<_, String>(1)?)
                    .map_err(|_| rusqlite::Error::InvalidColumnType(1, "added_at".to_string(), rusqlite::types::Type::Text))?
                    .with_timezone(&Utc),
                priority: row.get(2)?,
                last_crawled: row.get::<_, Option<String>>(3)?
                    .map(|s| DateTime::parse_from_rfc3339(&s).ok())
                    .flatten()
                    .map(|dt| dt.with_timezone(&Utc)),
                crawl_count: row.get(4)?,
            })
        })?;

        let mut seeds = Vec::new();
        for seed in seed_iter {
            seeds.push(seed?);
        }

        Ok(seeds)
    }

    pub async fn add_seed_urls(&self, urls: &[String]) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "INSERT OR IGNORE INTO seed_urls (url, added_at, priority) VALUES (?1, ?2, ?3)"
        )?;

        for url in urls {
            stmt.execute(params![
                url,
                Utc::now().to_rfc3339(),
                1
            ])?;
        }

        info!("Added {} new seed URLs", urls.len());
        Ok(())
    }

    pub async fn update_seed_url_crawled(&self, url: &str) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "UPDATE seed_urls SET last_crawled = ?, crawl_count = crawl_count + 1 WHERE url = ?",
            params![Utc::now().to_rfc3339(), url],
        )?;
        Ok(())
    }

    pub async fn get_dashboard_stats(&self) -> Result<DashboardStats> {
        let conn = self.conn.lock().unwrap();

        // Get basic counts
        let total_urls_crawled: i64 = conn.query_row(
            "SELECT COUNT(*) FROM crawl_results WHERE crawl_success = 1",
            [],
            |row| row.get(0),
        )?;

        let total_backlinks_found: i64 = conn.query_row(
            "SELECT COUNT(*) FROM backlinks",
            [],
            |row| row.get(0),
        )?;

        let unique_domains: i64 = conn.query_row(
            r#"
            SELECT COUNT(DISTINCT
                CASE
                    WHEN url LIKE 'http://%' THEN SUBSTR(url, 8, INSTR(SUBSTR(url, 8), '/') - 1)
                    WHEN url LIKE 'https://%' THEN SUBSTR(url, 9, INSTR(SUBSTR(url, 9), '/') - 1)
                    ELSE url
                END
            ) FROM crawl_results WHERE crawl_success = 1
            "#,
            [],
            |row| row.get(0),
        )?;

        // Calculate rates (simplified - last hour)
        let one_hour_ago = (Utc::now() - chrono::Duration::hours(1)).to_rfc3339();

        let crawl_rate_per_hour: f64 = conn.query_row(
            "SELECT COUNT(*) FROM crawl_results WHERE crawled_at > ?",
            params![one_hour_ago],
            |row| Ok(row.get::<_, i64>(0)? as f64),
        )?;

        let backlink_rate_per_hour: f64 = conn.query_row(
            "SELECT COUNT(*) FROM backlinks WHERE discovered_at > ?",
            params![one_hour_ago],
            |row| Ok(row.get::<_, i64>(0)? as f64),
        )?;

        // Get database size
        let page_count: i64 = conn.query_row("PRAGMA page_count", [], |row| row.get(0))?;
        let page_size: i64 = conn.query_row("PRAGMA page_size", [], |row| row.get(0))?;
        let database_size_mb = (page_count * page_size) as f64 / (1024.0 * 1024.0);

        // Get current mode and next switch from stats table
        let (current_mode, next_mode_switch) = conn.query_row(
            "SELECT current_mode, next_mode_switch FROM stats WHERE id = 1",
            [],
            |row| {
                let mode: String = row.get(0)?;
                let next_switch: Option<String> = row.get(1)?;
                let next_switch_dt = next_switch
                    .and_then(|s| DateTime::parse_from_rfc3339(&s).ok())
                    .map(|dt| dt.with_timezone(&Utc))
                    .unwrap_or_else(|| Utc::now());
                Ok((mode, next_switch_dt))
            },
        )?;

        Ok(DashboardStats {
            total_urls_crawled,
            total_backlinks_found,
            unique_domains,
            crawl_rate_per_hour,
            backlink_rate_per_hour,
            database_size_mb,
            system_memory_usage: 0.0, // TODO: Get from sysinfo
            system_cpu_usage: 0.0,    // TODO: Get from sysinfo
            last_updated: Utc::now(),
            current_mode,
            next_mode_switch,
        })
    }

    pub async fn update_stats(&self, stats: &DashboardStats) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            r#"
            UPDATE stats SET
                total_urls_crawled = ?,
                total_backlinks_found = ?,
                unique_domains = ?,
                crawl_rate_per_hour = ?,
                backlink_rate_per_hour = ?,
                database_size_mb = ?,
                system_memory_usage = ?,
                system_cpu_usage = ?,
                last_updated = ?,
                current_mode = ?,
                next_mode_switch = ?
            WHERE id = 1
            "#,
            params![
                stats.total_urls_crawled,
                stats.total_backlinks_found,
                stats.unique_domains,
                stats.crawl_rate_per_hour,
                stats.backlink_rate_per_hour,
                stats.database_size_mb,
                stats.system_memory_usage,
                stats.system_cpu_usage,
                stats.last_updated.to_rfc3339(),
                stats.current_mode,
                stats.next_mode_switch.to_rfc3339(),
            ],
        )?;
        Ok(())
    }

    pub async fn get_recent_crawls(&self, limit: i32) -> Result<Vec<CrawlResult>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            r#"
            SELECT url, original_url, redirect_chain, title, meta_description, content_text, content_html,
                   content_hash, word_count, page_size, http_status_code, response_time_ms, language,
                   charset, h1_tags, h2_tags, meta_keywords, canonical_url, robots_meta,
                   internal_links_count, external_links_count, images_count, content_type,
                   file_extension, crawl_success, error_message, crawled_at
            FROM crawl_results
            ORDER BY crawled_at DESC
            LIMIT ?
            "#,
        )?;

        let crawl_iter = stmt.query_map(params![limit], |row| {
            Ok(CrawlResult {
                url: row.get(0)?,
                original_url: row.get(1)?,
                redirect_chain: row.get::<_, Option<String>>(2)?
                    .and_then(|s| serde_json::from_str(&s).ok()),
                title: row.get(3)?,
                meta_description: row.get(4)?,
                content_text: row.get(5)?,
                content_html: row.get(6)?,
                content_hash: row.get(7)?,
                word_count: row.get(8)?,
                page_size: row.get(9)?,
                http_status_code: row.get(10)?,
                response_time_ms: row.get(11)?,
                language: row.get(12)?,
                charset: row.get(13)?,
                h1_tags: row.get::<_, Option<String>>(14)?
                    .and_then(|s| serde_json::from_str(&s).ok()),
                h2_tags: row.get::<_, Option<String>>(15)?
                    .and_then(|s| serde_json::from_str(&s).ok()),
                meta_keywords: row.get::<_, Option<String>>(16)?
                    .and_then(|s| serde_json::from_str(&s).ok()),
                canonical_url: row.get(17)?,
                robots_meta: row.get(18)?,
                internal_links_count: row.get(19)?,
                external_links_count: row.get(20)?,
                images_count: row.get(21)?,
                content_type: row.get(22)?,
                file_extension: row.get(23)?,
                crawl_success: row.get(24)?,
                error_message: row.get(25)?,
                crawled_at: DateTime::parse_from_rfc3339(&row.get::<_, String>(26)?)
                    .map_err(|_| rusqlite::Error::InvalidColumnType(26, "crawled_at".to_string(), rusqlite::types::Type::Text))?
                    .with_timezone(&Utc),
            })
        })?;

        let mut results = Vec::new();
        for result in crawl_iter {
            results.push(result?);
        }

        Ok(results)
    }
}
