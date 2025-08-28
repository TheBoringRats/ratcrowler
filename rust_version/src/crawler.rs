use reqwest::Client;
use scraper::{Html, Selector};
use std::collections::{HashSet, BinaryHeap, HashMap};
use std::time::{Duration, Instant};
use std::cmp::Ordering;
use url::{Url, ParseError};
use regex::Regex;
use crate::models::*;
use crate::database::WebsiteCrawlerDatabase;

#[derive(Eq, PartialEq)]
struct UrlPriority {
    url: String,
    priority: i32,
    depth: usize,
}

impl Ord for UrlPriority {
    fn cmp(&self, other: &Self) -> Ordering {
        // Higher priority first, then lower depth
        other.priority.cmp(&self.priority)
            .then_with(|| self.depth.cmp(&other.depth))
    }
}

impl PartialOrd for UrlPriority {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

pub struct WebsiteCrawler {
    client: Client,
    user_agent: String,
    timeout: Duration,
    max_redirects: usize,
    max_depth: usize,
    max_pages: usize,
    delay_ms: u64,
    respect_robots_txt: bool,
    robots_cache: HashMap<String, RobotsTxt>,
}

impl WebsiteCrawler {
    pub fn new(config: &CrawlConfig) -> Self {
        let client = Client::builder()
            .user_agent(&config.user_agent)
            .timeout(Duration::from_secs(config.timeout_secs))
            .redirect(reqwest::redirect::Policy::limited(config.max_redirects))
            .build()
            .expect("Failed to build HTTP client");

        Self {
            client,
            user_agent: config.user_agent.clone(),
            timeout: Duration::from_secs(config.timeout_secs),
            max_redirects: config.max_redirects,
            max_depth: config.max_depth,
            max_pages: config.max_pages,
            delay_ms: config.delay_ms,
            respect_robots_txt: config.respect_robots_txt,
            robots_cache: HashMap::new(),
        }
    }

    pub async fn crawl(&mut self, seed_urls: Vec<String>, database: &mut WebsiteCrawlerDatabase) -> Result<CrawlResult, CrawlError> {
        println!("🔍 Debug: Starting crawl with {} seed URLs", seed_urls.len());
        for (i, url) in seed_urls.iter().enumerate() {
            println!("🔍 Debug: Seed URL {}: {}", i + 1, url);
        }

        let session_id = database.create_crawl_session(&seed_urls, &serde_json::to_value(CrawlConfig::default())?)?;
        println!("🔍 Debug: Created session with ID: {}", session_id);

        let mut visited_urls = HashSet::new();
        let mut url_queue = BinaryHeap::new();
        let mut crawled_pages = Vec::new();
        let mut errors = Vec::new();

        // Initialize queue with seed URLs
        for url in seed_urls {
            println!("🔍 Debug: Adding to queue: {}", url);
            url_queue.push(UrlPriority {
                url,
                priority: 10, // High priority for seed URLs
                depth: 0,
            });
        }

        println!("🔍 Debug: Initial queue size: {}", url_queue.len());

        while let Some(url_priority) = url_queue.pop() {
            println!("🔍 Debug: Processing URL: {} (depth: {}, priority: {})", url_priority.url, url_priority.depth, url_priority.priority);

            if visited_urls.len() >= self.max_pages || url_priority.depth > self.max_depth {
                println!("🔍 Debug: Skipping due to limits - visited: {}, max_pages: {}, depth: {}, max_depth: {}",
                    visited_urls.len(), self.max_pages, url_priority.depth, self.max_depth);
                continue;
            }

            let url = url_priority.url;

            if visited_urls.contains(&url) {
                println!("🔍 Debug: Already visited: {}", url);
                continue;
            }

            visited_urls.insert(url.clone());
            println!("🔍 Debug: Marked as visited: {}", url);

            // Check robots.txt if enabled
            if self.respect_robots_txt {
                if let Ok(false) = self.can_crawl(&url).await {
                    continue;
                }
            }

            // Add delay between requests
            if self.delay_ms > 0 {
                tokio::time::sleep(Duration::from_millis(self.delay_ms)).await;
            }

            match self.crawl_single_page(&url, url_priority.depth).await {
                Ok(page) => {
                    println!("🔍 Debug: Successfully crawled page: {} (status: {}, size: {} bytes)",
                        page.url, page.http_status_code, page.page_size);

                    // Store page in database
                    if let Err(e) = database.store_crawled_page(&page, &session_id) {
                        println!("🔍 Debug: Database error storing page: {:?}", e);
                        errors.push(CrawlError::DatabaseError(e.to_string()));
                        continue;
                    }

                    crawled_pages.push(page.clone());

                    // Extract and queue new URLs
                    if url_priority.depth < self.max_depth {
                        let new_urls = self.extract_urls(&page.content_html, &url);
                        println!("🔍 Debug: Extracted {} new URLs from {}", new_urls.len(), url);
                        for new_url in new_urls {
                            if !visited_urls.contains(&new_url) {
                                let priority = self.calculate_url_priority(&new_url, &url);
                                url_queue.push(UrlPriority {
                                    url: new_url,
                                    priority,
                                    depth: url_priority.depth + 1,
                                });
                            }
                        }
                    }
                }
                Err(e) => {
                    println!("🔍 Debug: Error crawling page {}: {:?}", url, e);

                    // Log error
                    if let Err(db_err) = database.log_crawl_error(
                        &session_id,
                        &url,
                        &format!("{:?}", e),
                        &e.to_string(),
                        None,
                    ) {
                        errors.push(CrawlError::DatabaseError(db_err.to_string()));
                    }
                    errors.push(e);
                }
            }
        }

        // Finish crawl session
        let _ = database.finish_crawl_session(&session_id, "completed");

        Ok(CrawlResult {
            session_id,
            pages_crawled: crawled_pages.len(),
            errors: errors.len(),
            duration: Duration::from_secs(0), // Would need to track actual duration
        })
    }

    async fn crawl_single_page(&self, url: &str, _depth: usize) -> Result<CrawledPage, CrawlError> {
        println!("🔍 Debug: Starting to crawl single page: {}", url);
        let start_time = Instant::now();

        let response = self.client.get(url).send().await?;
        let status_code = response.status().as_u16();
        let response_time = start_time.elapsed();
        let charset = self.detect_charset_from_headers(&response);

        println!("🔍 Debug: HTTP response received - status: {}, time: {:?}", status_code, response_time);

        if !response.status().is_success() {
            println!("🔍 Debug: HTTP error - status: {}", status_code);
            return Err(CrawlError::HttpError(status_code, response.status().to_string()));
        }

        let html = response.text().await?;
        println!("🔍 Debug: Downloaded HTML content - size: {} bytes", html.len());
        let document = Html::parse_document(&html);

        let page = CrawledPage {
            url: url.to_string(),
            original_url: url.to_string(),
            redirect_chain: Vec::new(),
            title: self.extract_title(&document),
            meta_description: self.extract_meta_description(&document),
            content_text: self.extract_text_content(&document),
            content_html: html.clone(),
            content_hash: self.calculate_content_hash(&html),
            word_count: self.count_words(&html),
            page_size: html.len(),
            http_status_code: status_code,
            response_time_ms: response_time.as_millis() as u64,
            language: self.detect_language(&document),
            charset,
            h1_tags: self.extract_h1_tags(&document),
            h2_tags: self.extract_h2_tags(&document),
            meta_keywords: self.extract_meta_keywords(&document),
            canonical_url: self.extract_canonical_url(&document),
            robots_meta: self.extract_robots_meta(&document),
            internal_links_count: 0, // Will be calculated after URL extraction
            external_links_count: 0, // Will be calculated after URL extraction
            images_count: self.count_images(&document),
            crawl_time: chrono::Utc::now(),
        };

        println!("🔍 Debug: Successfully created CrawledPage for: {}", url);
        Ok(page)
    }

    async fn can_crawl(&mut self, url: &str) -> Result<bool, CrawlError> {
        let parsed_url = Url::parse(url)?;
        let robots_url = format!("{}/robots.txt", parsed_url.origin().unicode_serialization());

        if !self.robots_cache.contains_key(&robots_url) {
            let robots_txt = self.fetch_robots_txt(&robots_url).await?;
            self.robots_cache.insert(robots_url.clone(), robots_txt);
        }

        if let Some(robots_txt) = self.robots_cache.get(&robots_url) {
            Ok(robots_txt.can_crawl(&self.user_agent, &parsed_url.path()))
        } else {
            Ok(true) // Allow crawling if robots.txt can't be fetched
        }
    }

    async fn fetch_robots_txt(&self, robots_url: &str) -> Result<RobotsTxt, CrawlError> {
        match self.client.get(robots_url).send().await {
            Ok(response) if response.status().is_success() => {
                let content = response.text().await?;
                Ok(RobotsTxt::parse(&content))
            }
            _ => Ok(RobotsTxt::default()), // Default allows all
        }
    }

    fn extract_title(&self, document: &Html) -> String {
        let selector = Selector::parse("title").unwrap();
        document.select(&selector)
            .next()
            .map(|el| el.text().collect::<String>().trim().to_string())
            .unwrap_or_default()
    }

    fn extract_meta_description(&self, document: &Html) -> String {
        let selector = Selector::parse("meta[name='description']").unwrap();
        document.select(&selector)
            .next()
            .and_then(|el| el.value().attr("content"))
            .unwrap_or_default()
            .to_string()
    }

    fn extract_text_content(&self, document: &Html) -> String {
        let selector = Selector::parse("body").unwrap();
        document.select(&selector)
            .next()
            .map(|el| el.text().collect::<String>())
            .unwrap_or_default()
    }

    fn calculate_content_hash(&self, content: &str) -> String {
        use sha2::{Sha256, Digest};
        let mut hasher = Sha256::new();
        hasher.update(content);
        format!("{:x}", hasher.finalize())
    }

    fn count_words(&self, html: &str) -> usize {
        let document = Html::parse_fragment(html);
        let body_selector = Selector::parse("body").unwrap();
        let text_content = if let Some(body) = document.select(&body_selector).next() {
            body.text().collect::<String>()
        } else {
            // Fallback to all text in the document
            let mut all_text = String::new();
            for text in document.root_element().text() {
                all_text.push_str(text);
                all_text.push(' ');
            }
            all_text
        };
        text_content.split_whitespace().count()
    }

    fn detect_language(&self, document: &Html) -> String {
        let selector = Selector::parse("html").unwrap();
        document.select(&selector)
            .next()
            .and_then(|el| el.value().attr("lang"))
            .unwrap_or("en")
            .to_string()
    }

    fn detect_charset_from_headers(&self, response: &reqwest::Response) -> String {
        response.headers()
            .get("content-type")
            .and_then(|ct| ct.to_str().ok())
            .and_then(|ct| {
                ct.split(';')
                    .find(|s| s.trim().starts_with("charset="))
                    .map(|s| s.trim().trim_start_matches("charset=").to_string())
            })
            .unwrap_or_else(|| "utf-8".to_string())
    }

    fn extract_h1_tags(&self, document: &Html) -> Vec<String> {
        let selector = Selector::parse("h1").unwrap();
        document.select(&selector)
            .map(|el| el.text().collect::<String>().trim().to_string())
            .filter(|s| !s.is_empty())
            .collect()
    }

    fn extract_h2_tags(&self, document: &Html) -> Vec<String> {
        let selector = Selector::parse("h2").unwrap();
        document.select(&selector)
            .map(|el| el.text().collect::<String>().trim().to_string())
            .filter(|s| !s.is_empty())
            .collect()
    }

    fn extract_meta_keywords(&self, document: &Html) -> String {
        let selector = Selector::parse("meta[name='keywords']").unwrap();
        document.select(&selector)
            .next()
            .and_then(|el| el.value().attr("content"))
            .unwrap_or_default()
            .to_string()
    }

    fn extract_canonical_url(&self, document: &Html) -> String {
        let selector = Selector::parse("link[rel='canonical']").unwrap();
        document.select(&selector)
            .next()
            .and_then(|el| el.value().attr("href"))
            .unwrap_or_default()
            .to_string()
    }

    fn extract_robots_meta(&self, document: &Html) -> String {
        let selector = Selector::parse("meta[name='robots']").unwrap();
        document.select(&selector)
            .next()
            .and_then(|el| el.value().attr("content"))
            .unwrap_or_default()
            .to_string()
    }

    fn count_images(&self, document: &Html) -> usize {
        let selector = Selector::parse("img").unwrap();
        document.select(&selector).count()
    }

    fn extract_urls(&self, html: &str, base_url: &str) -> Vec<String> {
        let document = Html::parse_document(html);
        let selector = Selector::parse("a[href]").unwrap();
        let mut urls = Vec::new();

        for element in document.select(&selector) {
            if let Some(href) = element.value().attr("href") {
                if let Ok(absolute_url) = self.resolve_url(base_url, href) {
                    urls.push(absolute_url.to_string());
                }
            }
        }

        urls
    }

    fn resolve_url(&self, base_url: &str, href: &str) -> Result<Url, ParseError> {
        let base = Url::parse(base_url)?;
        base.join(href)
    }

    fn calculate_url_priority(&self, url: &str, referrer: &str) -> i32 {
        let mut priority = 5; // Base priority

        // Higher priority for same domain
        if let (Ok(url_domain), Ok(ref_domain)) = (
            self.extract_domain(url),
            self.extract_domain(referrer)
        ) {
            if url_domain == ref_domain {
                priority += 3;
            }
        }

        // Higher priority for important paths
        if url.contains("/about") || url.contains("/contact") || url.contains("/services") {
            priority += 2;
        }

        priority
    }

    fn extract_domain(&self, url: &str) -> Result<String, ParseError> {
        let parsed = Url::parse(url)?;
        Ok(parsed.host_str().unwrap_or("").to_string())
    }
}

#[derive(Debug, Default)]
struct RobotsTxt {
    rules: HashMap<String, Vec<String>>,
}

impl RobotsTxt {
    fn parse(content: &str) -> Self {
        let mut rules = HashMap::new();
        let mut current_user_agent = "*".to_string();

        for line in content.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }

            if line.to_lowercase().starts_with("user-agent:") {
                current_user_agent = line.split(':').nth(1).unwrap_or("*").trim().to_string();
            } else if line.to_lowercase().starts_with("disallow:") {
                if let Some(path) = line.split(':').nth(1) {
                    let path = path.trim();
                    if !path.is_empty() {
                        rules.entry(current_user_agent.clone())
                            .or_insert_with(Vec::new)
                            .push(path.to_string());
                    }
                }
            }
        }

        Self { rules }
    }

    fn can_crawl(&self, user_agent: &str, path: &str) -> bool {
        // Check specific user agent rules first, then wildcard
        let user_agents = [user_agent, "*"];

        for ua in &user_agents {
            if let Some(disallowed_paths) = self.rules.get(&ua.to_string()) {
                for disallowed in disallowed_paths {
                    if path.starts_with(disallowed) {
                        return false;
                    }
                }
            }
        }

        true
    }
}
