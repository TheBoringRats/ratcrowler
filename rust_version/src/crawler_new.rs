use crate::models::{CrawlResult, CrawlerConfig};
use crate::database::Database;
use anyhow::Result;
use chrono::Utc;
use futures::future::join_all;
use log::{info, warn, error, debug};
use reqwest::{Client, ClientBuilder};
use scraper::{Html, Selector};
use std::collections::HashSet;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::Semaphore;
use tokio::time::sleep;
use url::Url;
use rand::seq::SliceRandom;
use sha2::{Sha256, Digest};

pub struct Crawler {
    client: Client,
    database: Arc<Database>,
    config: CrawlerConfig,
    semaphore: Arc<Semaphore>,
    visited_urls: Arc<tokio::sync::Mutex<HashSet<String>>>,
}

impl Crawler {
    pub fn new(database: Arc<Database>, config: CrawlerConfig) -> Result<Self> {
        let client = ClientBuilder::new()
            .timeout(Duration::from_secs(config.request_timeout_seconds))
            .user_agent(&config.user_agents[0])
            .gzip(true)
            .brotli(true)
            .build()?;

        Ok(Self {
            client,
            database,
            semaphore: Arc::new(Semaphore::new(config.max_concurrent_requests)),
            config,
            visited_urls: Arc::new(tokio::sync::Mutex::new(HashSet::new())),
        })
    }

    pub async fn crawl_for_duration(&self, duration_hours: u64) -> Result<usize> {
        info!("Starting crawling for {} hours", duration_hours);
        let start_time = Instant::now();
        let duration = Duration::from_secs(duration_hours * 3600);

        let mut total_crawled = 0;
        let mut current_urls = Vec::new();

        while start_time.elapsed() < duration {
            // Get seed URLs if we don't have any current URLs
            if current_urls.is_empty() {
                let seed_urls = self.database.get_seed_urls(20).await?;
                current_urls = seed_urls.into_iter().map(|s| s.url).collect();

                if current_urls.is_empty() {
                    warn!("No seed URLs available for crawling");
                    sleep(Duration::from_secs(60)).await;
                    continue;
                }
            }

            // Process URLs in batches
            let batch_size = self.config.max_concurrent_requests.min(current_urls.len());
            let batch: Vec<_> = current_urls.drain(..batch_size).collect();

            let tasks: Vec<_> = batch.into_iter().map(|url| {
                let crawler = self.clone();
                async move {
                    crawler.crawl_url(&url).await
                }
            }).collect();

            let results = join_all(tasks).await;

            for result in results {
                match result {
                    Ok((crawl_result, discovered_urls)) => {
                        total_crawled += 1;

                        // Save crawl result to database
                        if let Err(e) = self.database.save_crawl_result(&crawl_result).await {
                            error!("Failed to save crawl result: {}", e);
                        }

                        // Update seed URL crawl status
                        if let Err(e) = self.database.update_seed_url_crawled(&crawl_result.url).await {
                            warn!("Failed to update seed URL status: {}", e);
                        }

                        // Add discovered URLs to our queue (limit to prevent explosion)
                        let filtered_urls: Vec<_> = discovered_urls
                            .into_iter()
                            .filter(|url| self.is_crawlable_url(url))
                            .take(5) // Limit per page
                            .collect();

                        current_urls.extend(filtered_urls);

                        // Also add unique domains to seed URLs
                        if let Ok(unique_urls) = self.extract_unique_domains(&current_urls).await {
                            if !unique_urls.is_empty() {
                                if let Err(e) = self.database.add_seed_urls(&unique_urls).await {
                                    warn!("Failed to add new seed URLs: {}", e);
                                }
                            }
                        }
                    }
                    Err(e) => {
                        error!("Failed to crawl URL: {}", e);
                    }
                }
            }

            info!("Crawled {} URLs so far", total_crawled);

            // Check if we should continue
            if start_time.elapsed() >= duration {
                break;
            }

            // Small delay before next batch
            sleep(Duration::from_millis(500)).await;
        }

        info!("Crawling completed. Total URLs crawled: {}", total_crawled);
        Ok(total_crawled)
    }

    async fn crawl_url(&self, url: &str) -> Result<(CrawlResult, Vec<String>)> {
        // Check if already visited
        {
            let visited = self.visited_urls.lock().await;
            if visited.contains(url) {
                return Err(anyhow::anyhow!("URL already visited"));
            }
        }

        // Get permit for concurrent request
        let _permit = self.semaphore.acquire().await?;

        // Mark as visited
        {
            let mut visited = self.visited_urls.lock().await;
            visited.insert(url.to_string());
        }

        let start_time = Instant::now();

        // Select random user agent
        let user_agent = self.config.user_agents
            .choose(&mut rand::thread_rng())
            .unwrap_or(&self.config.user_agents[0]);

        let response = self.client
            .get(url)
            .header("User-Agent", user_agent)
            .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            .header("Accept-Language", "en-US,en;q=0.5")
            .header("Accept-Encoding", "gzip, deflate, br")
            .header("DNT", "1")
            .header("Connection", "keep-alive")
            .header("Upgrade-Insecure-Requests", "1")
            .send()
            .await?;

        let response_time_ms = start_time.elapsed().as_millis() as i32;
        let status_code = response.status().as_u16() as i32;
        let final_url = response.url().to_string();

        if !response.status().is_success() {
            return Ok((CrawlResult {
                url: url.to_string(),
                original_url: Some(final_url),
                redirect_chain: None,
                title: None,
                meta_description: None,
                content_text: None,
                content_html: None,
                content_hash: None,
                word_count: None,
                page_size: None,
                http_status_code: Some(status_code),
                response_time_ms: Some(response_time_ms),
                language: None,
                charset: None,
                h1_tags: None,
                h2_tags: None,
                meta_keywords: None,
                canonical_url: None,
                robots_meta: None,
                internal_links_count: None,
                external_links_count: None,
                images_count: None,
                content_type: None,
                file_extension: None,
                crawl_success: false,
                error_message: Some(format!("HTTP error: {}", status_code)),
                crawled_at: Utc::now(),
            }, Vec::new()));
        }

        let body = response.text().await?;
        let document = Html::parse_document(&body);

        // Extract page information
        let title = self.extract_title(&document);
        let meta_description = self.extract_meta_description(&document);
        let content_text = self.extract_text_content(&document);
        let h1_tags = self.extract_headings(&document, "h1");
        let h2_tags = self.extract_headings(&document, "h2");
        let meta_keywords = self.extract_meta_keywords(&document);
        let canonical_url = self.extract_canonical_url(&document);
        let robots_meta = self.extract_robots_meta(&document);
        let discovered_links = self.extract_links(&document, url);

        // Calculate metrics
        let word_count = content_text.split_whitespace().count() as i32;
        let page_size = body.len() as i32;
        let content_hash = format!("{:x}", Sha256::digest(body.as_bytes()));

        // Count links and images
        let internal_links_count = self.count_internal_links(&discovered_links, url);
        let external_links_count = discovered_links.len() as i32 - internal_links_count;
        let images_count = self.count_images(&document);

        let crawl_result = CrawlResult {
            url: url.to_string(),
            original_url: if final_url != url { Some(final_url) } else { None },
            redirect_chain: None, // TODO: Track redirect chain
            title: Some(title),
            meta_description: Some(meta_description),
            content_text: Some(content_text),
            content_html: Some(body),
            content_hash: Some(content_hash),
            word_count: Some(word_count),
            page_size: Some(page_size),
            http_status_code: Some(status_code),
            response_time_ms: Some(response_time_ms),
            language: None, // TODO: Detect language
            charset: None,  // TODO: Extract charset
            h1_tags: Some(h1_tags),
            h2_tags: Some(h2_tags),
            meta_keywords: Some(meta_keywords),
            canonical_url: Some(canonical_url),
            robots_meta: Some(robots_meta),
            internal_links_count: Some(internal_links_count),
            external_links_count: Some(external_links_count),
            images_count: Some(images_count),
            content_type: None, // TODO: Extract content type
            file_extension: None, // TODO: Extract file extension
            crawl_success: true,
            error_message: None,
            crawled_at: Utc::now(),
        };

        // Respect delay
        sleep(Duration::from_millis(self.config.delay_between_requests_ms)).await;

        Ok((crawl_result, discovered_links))
    }

    fn extract_title(&self, document: &Html) -> String {
        let title_selector = Selector::parse("title").unwrap();
        document
            .select(&title_selector)
            .next()
            .map(|el| el.text().collect::<String>())
            .unwrap_or_default()
            .trim()
            .to_string()
    }

    fn extract_meta_description(&self, document: &Html) -> String {
        let meta_selector = Selector::parse("meta[name='description']").unwrap();
        document
            .select(&meta_selector)
            .next()
            .and_then(|el| el.value().attr("content"))
            .unwrap_or_default()
            .trim()
            .to_string()
    }

    fn extract_text_content(&self, document: &Html) -> String {
        // Remove script and style elements first
        let mut text_parts = Vec::new();

        let body_selector = Selector::parse("body").unwrap();
        if let Some(body) = document.select(&body_selector).next() {
            let text: String = body.text().collect::<Vec<_>>().join(" ");
            text_parts.push(text);
        }

        text_parts.join(" ")
            .split_whitespace()
            .collect::<Vec<_>>()
            .join(" ")
    }

    fn extract_headings(&self, document: &Html, tag: &str) -> Vec<String> {
        let selector = Selector::parse(tag).unwrap();
        document
            .select(&selector)
            .map(|el| el.text().collect::<String>().trim().to_string())
            .filter(|s| !s.is_empty())
            .collect()
    }

    fn extract_meta_keywords(&self, document: &Html) -> Vec<String> {
        let meta_selector = Selector::parse("meta[name='keywords']").unwrap();
        document
            .select(&meta_selector)
            .next()
            .and_then(|el| el.value().attr("content"))
            .unwrap_or_default()
            .split(',')
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect()
    }

    fn extract_canonical_url(&self, document: &Html) -> String {
        let canonical_selector = Selector::parse("link[rel='canonical']").unwrap();
        document
            .select(&canonical_selector)
            .next()
            .and_then(|el| el.value().attr("href"))
            .unwrap_or_default()
            .to_string()
    }

    fn extract_robots_meta(&self, document: &Html) -> String {
        let robots_selector = Selector::parse("meta[name='robots']").unwrap();
        document
            .select(&robots_selector)
            .next()
            .and_then(|el| el.value().attr("content"))
            .unwrap_or_default()
            .to_string()
    }

    fn extract_links(&self, document: &Html, base_url: &str) -> Vec<String> {
        let link_selector = Selector::parse("a[href]").unwrap();
        let mut links = Vec::new();

        for element in document.select(&link_selector) {
            if let Some(href) = element.value().attr("href") {
                match Url::parse(href).or_else(|_| Url::parse(base_url)?.join(href)) {
                    Ok(url) => {
                        let url_str = url.to_string();
                        if self.is_crawlable_url(&url_str) {
                            links.push(url_str);
                        }
                    }
                    Err(_) => continue,
                }
            }
        }

        links
    }

    fn count_internal_links(&self, links: &[String], base_url: &str) -> i32 {
        if let Ok(base) = Url::parse(base_url) {
            if let Some(base_domain) = base.host_str() {
                return links.iter().filter(|link| {
                    if let Ok(url) = Url::parse(link) {
                        url.host_str() == Some(base_domain)
                    } else {
                        false
                    }
                }).count() as i32;
            }
        }
        0
    }

    fn count_images(&self, document: &Html) -> i32 {
        let img_selector = Selector::parse("img").unwrap();
        document.select(&img_selector).count() as i32
    }

    fn is_crawlable_url(&self, url: &str) -> bool {
        if let Ok(parsed_url) = Url::parse(url) {
            // Only HTTP/HTTPS
            if !matches!(parsed_url.scheme(), "http" | "https") {
                return false;
            }

            // Avoid certain file extensions
            if let Some(path) = parsed_url.path_segments() {
                if let Some(last_segment) = path.last() {
                    let extensions_to_avoid = [
                        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
                        "zip", "rar", "7z", "tar", "gz", "bz2",
                        "mp3", "mp4", "avi", "mov", "wmv", "flv",
                        "jpg", "jpeg", "png", "gif", "bmp", "svg", "ico",
                        "css", "js", "xml", "json", "csv",
                    ];

                    for ext in &extensions_to_avoid {
                        if last_segment.ends_with(&format!(".{}", ext)) {
                            return false;
                        }
                    }
                }
            }

            true
        } else {
            false
        }
    }

    async fn extract_unique_domains(&self, urls: &[String]) -> Result<Vec<String>> {
        let mut unique_domains = HashSet::new();
        let mut result = Vec::new();

        for url in urls {
            if let Ok(parsed_url) = Url::parse(url) {
                if let Some(domain) = parsed_url.host_str() {
                    if unique_domains.insert(domain.to_string()) {
                        // This is a new unique domain, add the base URL
                        let base_url = format!("{}://{}", parsed_url.scheme(), domain);
                        result.push(base_url);
                    }
                }
            }
        }

        Ok(result)
    }

    pub async fn get_stats(&self) -> Result<usize> {
        let visited_count = self.visited_urls.lock().await.len();
        Ok(visited_count)
    }
}

impl Clone for Crawler {
    fn clone(&self) -> Self {
        Self {
            client: self.client.clone(),
            database: self.database.clone(),
            config: self.config.clone(),
            semaphore: self.semaphore.clone(),
            visited_urls: self.visited_urls.clone(),
        }
    }
}
