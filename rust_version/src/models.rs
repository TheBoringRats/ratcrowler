use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacklinkData {
    pub source_url: String,
    pub target_url: String,
    pub anchor_text: String,
    pub context: String,
    pub page_title: String,
    pub domain_authority: f64,
    pub is_nofollow: bool,
    pub crawl_date: DateTime<Utc>,
}

impl BacklinkData {
    pub fn new(
        source_url: String,
        target_url: String,
        anchor_text: String,
        context: String,
        page_title: String,
    ) -> Self {
        Self {
            source_url,
            target_url,
            anchor_text,
            context,
            page_title,
            domain_authority: 0.0,
            is_nofollow: false,
            crawl_date: Utc::now(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrawledPage {
    pub url: String,
    pub original_url: String,
    pub redirect_chain: Vec<String>,
    pub title: String,
    pub meta_description: String,
    pub content_text: String,
    pub content_html: String,
    pub content_hash: String,
    pub word_count: usize,
    pub page_size: usize,
    pub http_status_code: u16,
    pub response_time_ms: u64,
    pub language: String,
    pub charset: String,
    pub h1_tags: Vec<String>,
    pub h2_tags: Vec<String>,
    pub meta_keywords: String,
    pub canonical_url: String,
    pub robots_meta: String,
    pub internal_links_count: usize,
    pub external_links_count: usize,
    pub images_count: usize,
    pub crawl_time: DateTime<Utc>,
}

impl CrawledPage {
    pub fn new(url: String, original_url: String) -> Self {
        Self {
            url,
            original_url,
            redirect_chain: vec![],
            title: String::new(),
            meta_description: String::new(),
            content_text: String::new(),
            content_html: String::new(),
            content_hash: String::new(),
            word_count: 0,
            page_size: 0,
            http_status_code: 0,
            response_time_ms: 0,
            language: String::new(),
            charset: String::new(),
            h1_tags: vec![],
            h2_tags: vec![],
            meta_keywords: String::new(),
            canonical_url: String::new(),
            robots_meta: String::new(),
            internal_links_count: 0,
            external_links_count: 0,
            images_count: 0,
            crawl_time: Utc::now(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrawlSession {
    pub id: String,
    pub start_time: DateTime<Utc>,
    pub seed_urls: Vec<String>,
    pub config: serde_json::Value,
    pub end_time: Option<DateTime<Utc>>,
    pub status: String,
}

impl CrawlSession {
    pub fn new(seed_urls: Vec<String>, config: serde_json::Value) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            start_time: Utc::now(),
            seed_urls,
            config,
            end_time: None,
            status: "running".to_string(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DomainScore {
    pub domain: String,
    pub authority_score: f64,
    pub total_backlinks: usize,
    pub unique_referring_domains: usize,
    pub last_updated: DateTime<Utc>,
}

impl DomainScore {
    pub fn new(domain: String) -> Self {
        Self {
            domain,
            authority_score: 0.0,
            total_backlinks: 0,
            unique_referring_domains: 0,
            last_updated: Utc::now(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PageRankScore {
    pub url: String,
    pub pagerank_score: f64,
    pub last_calculated: DateTime<Utc>,
}

impl PageRankScore {
    pub fn new(url: String, score: f64) -> Self {
        Self {
            url,
            pagerank_score: score,
            last_calculated: Utc::now(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, thiserror::Error)]
pub enum CrawlError {
    #[error("HTTP error: {0} - {1}")]
    HttpError(u16, String),
    #[error("Network error: {0}")]
    NetworkError(String),
    #[error("Timeout error: {0}")]
    TimeoutError(String),
    #[error("Parse error: {0}")]
    ParseError(String),
    #[error("Database error: {0}")]
    DatabaseError(String),
    #[error("IO error: {0}")]
    IoError(String),
    #[error("URL parse error: {0}")]
    UrlParseError(String),
    #[error("JSON error: {0}")]
    JsonError(String),
}

impl CrawlError {
    pub fn new(session_id: String, url: String, error_type: String, error_msg: String) -> Self {
        CrawlError::DatabaseError(format!("Session {}: {} - {}: {}", session_id, url, error_type, error_msg))
    }
}

impl From<reqwest::Error> for CrawlError {
    fn from(err: reqwest::Error) -> Self {
        if err.is_timeout() {
            CrawlError::TimeoutError(err.to_string())
        } else if err.is_connect() {
            CrawlError::NetworkError(err.to_string())
        } else {
            CrawlError::HttpError(0, err.to_string())
        }
    }
}

impl From<url::ParseError> for CrawlError {
    fn from(err: url::ParseError) -> Self {
        CrawlError::UrlParseError(err.to_string())
    }
}

impl From<rusqlite::Error> for CrawlError {
    fn from(err: rusqlite::Error) -> Self {
        CrawlError::DatabaseError(err.to_string())
    }
}

impl From<std::io::Error> for CrawlError {
    fn from(err: std::io::Error) -> Self {
        CrawlError::IoError(err.to_string())
    }
}

impl From<serde_json::Error> for CrawlError {
    fn from(err: serde_json::Error) -> Self {
        CrawlError::JsonError(err.to_string())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrawlConfig {
    pub user_agent: String,
    pub timeout_secs: u64,
    pub max_redirects: usize,
    pub max_depth: usize,
    pub max_pages: usize,
    pub delay_ms: u64,
    pub respect_robots_txt: bool,
}

impl Default for CrawlConfig {
    fn default() -> Self {
        Self {
            user_agent: "RatCrawler/1.0".to_string(),
            timeout_secs: 30,
            max_redirects: 5,
            max_depth: 3,
            max_pages: 100,
            delay_ms: 100,
            respect_robots_txt: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacklinkConfig {
    pub user_agent: String,
    pub timeout_secs: u64,
    pub max_redirects: usize,
}

impl Default for BacklinkConfig {
    fn default() -> Self {
        Self {
            user_agent: "RatCrawler-Backlinks/1.0".to_string(),
            timeout_secs: 60,
            max_redirects: 5,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrawlResult {
    pub session_id: String,
    pub pages_crawled: usize,
    pub errors: usize,
    pub duration: std::time::Duration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacklinkAnalysis {
    pub total_backlinks: usize,
    pub unique_domains: usize,
    pub spam_backlinks: usize,
    pub domain_authority: f64,
    pub pagerank_score: f64,
}

impl Default for BacklinkAnalysis {
    fn default() -> Self {
        Self {
            total_backlinks: 0,
            unique_domains: 0,
            spam_backlinks: 0,
            domain_authority: 0.0,
            pagerank_score: 0.0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntegratedCrawlConfig {
    pub web_crawl_config: CrawlConfig,
    pub backlink_config: BacklinkConfig,
    pub max_backlink_analyses: usize,
    pub backlink_timeout_secs: u64,
}

impl Default for IntegratedCrawlConfig {
    fn default() -> Self {
        Self {
            web_crawl_config: CrawlConfig::default(),
            backlink_config: BacklinkConfig::default(),
            max_backlink_analyses: 10,
            backlink_timeout_secs: 60,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntegratedCrawlResult {
    pub web_crawl_result: CrawlResult,
    pub backlink_analyses: Vec<(String, BacklinkAnalysis)>,
    pub report: CrawlReport,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DomainAnalysis {
    pub domain: String,
    pub pages_crawled: usize,
    pub backlink_analysis: BacklinkAnalysis,
    pub domain_authority: f64,
    pub crawl_errors: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrawlReport {
    pub total_pages_crawled: usize,
    pub total_backlinks_found: usize,
    pub total_unique_domains: usize,
    pub total_spam_backlinks: usize,
    pub average_domain_authority: f64,
    pub crawl_errors: usize,
    pub backlink_analyses_completed: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrawlStatistics {
    pub total_pages_crawled: usize,
    pub total_crawl_errors: usize,
    pub database_size_mb: f64,
    pub last_crawl_time: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduledCrawl {
    pub name: String,
    pub urls: Vec<String>,
    pub schedule: CrawlSchedule,
    pub last_run: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CrawlSchedule {
    Daily,
    Weekly,
    Monthly,
    Custom(String),
}
