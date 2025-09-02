use crate::models::{BacklinkData, CrawlerConfig};
use crate::database::Database;
use anyhow::Result;
use chrono::Utc;
use futures::future::join_all;
use log::{info, warn, error, debug};
use reqwest::{Client, ClientBuilder};
use scraper::{Html, Selector};
use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::Semaphore;
use tokio::time::sleep;
use url::{Url, ParseError};
use rand::seq::SliceRandom;

pub struct BacklinkProcessor {
    client: Client,
    database: Arc<Database>,
    config: CrawlerConfig,
    semaphore: Arc<Semaphore>,
    visited_urls: Arc<tokio::sync::Mutex<HashSet<String>>>,
    discovered_backlinks: Arc<tokio::sync::Mutex<Vec<BacklinkData>>>,
}

impl BacklinkProcessor {
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
            discovered_backlinks: Arc::new(tokio::sync::Mutex::new(Vec::new())),
        })
    }

    pub async fn process_backlinks_for_duration(&self, duration_hours: u64) -> Result<usize> {
        info!("Starting backlink processing for {} hours", duration_hours);
        let start_time = Instant::now();
        let duration = Duration::from_secs(duration_hours * 3600);
        
        let mut total_backlinks = 0;
        let mut processed_urls = 0;

        while start_time.elapsed() < duration {
            // Get seed URLs from database
            let seed_urls = self.database.get_seed_urls(50).await?;
            
            if seed_urls.is_empty() {
                warn!("No seed URLs available for backlink processing");
                sleep(Duration::from_secs(60)).await;
                continue;
            }

            // Process backlinks for each seed URL
            let tasks: Vec<_> = seed_urls.into_iter().map(|seed_url| {
                let processor = self.clone();
                async move {
                    processor.discover_backlinks_for_url(&seed_url.url, 3).await
                }
            }).collect();

            let results = join_all(tasks).await;
            
            for result in results {
                match result {
                    Ok(backlinks) => {
                        total_backlinks += backlinks.len();
                        processed_urls += 1;
                        
                        // Save backlinks to database
                        if let Err(e) = self.database.save_backlinks(&backlinks).await {
                            error!("Failed to save backlinks: {}", e);
                        }
                        
                        // Update seed URLs with unique URLs found
                        self.update_seed_urls_from_backlinks(&backlinks).await?;
                    }
                    Err(e) => {
                        error!("Failed to process backlinks: {}", e);
                    }
                }
            }

            info!("Processed {} URLs, found {} backlinks so far", processed_urls, total_backlinks);
            
            // Check if we should continue
            if start_time.elapsed() >= duration {
                break;
            }
            
            // Small delay before next batch
            sleep(Duration::from_secs(30)).await;
        }

        info!("Backlink processing completed. Total backlinks found: {}", total_backlinks);
        Ok(total_backlinks)
    }

    async fn discover_backlinks_for_url(&self, url: &str, max_depth: u32) -> Result<Vec<BacklinkData>> {
        let mut discovered = Vec::new();
        let mut queue = vec![(url.to_string(), 0)];
        let mut visited = HashSet::new();

        while let Some((current_url, depth)) = queue.pop() {
            if depth >= max_depth || visited.contains(&current_url) {
                continue;
            }

            visited.insert(current_url.clone());
            
            // Get permit for concurrent request
            let _permit = self.semaphore.acquire().await?;
            
            match self.extract_backlinks_from_page(&current_url).await {
                Ok((backlinks, outbound_links)) => {
                    discovered.extend(backlinks);
                    
                    // Add outbound links to queue for further processing
                    for link in outbound_links.into_iter().take(5) { // Limit to 5 per page
                        if !visited.contains(&link) {
                            queue.push((link, depth + 1));
                        }
                    }
                }
                Err(e) => {
                    debug!("Failed to extract backlinks from {}: {}", current_url, e);
                }
            }

            // Respect delay
            sleep(Duration::from_millis(self.config.delay_between_requests_ms)).await;
        }

        Ok(discovered)
    }

    async fn extract_backlinks_from_page(&self, url: &str) -> Result<(Vec<BacklinkData>, Vec<String>)> {
        let user_agent = self.config.user_agents
            .choose(&mut rand::thread_rng())
            .unwrap_or(&self.config.user_agents[0]);

        let response = self.client
            .get(url)
            .header("User-Agent", user_agent)
            .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            .header("Accept-Language", "en-US,en;q=0.5")
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(anyhow::anyhow!("HTTP error: {}", response.status()));
        }

        let body = response.text().await?;
        let document = Html::parse_document(&body);
        
        let mut backlinks = Vec::new();
        let mut outbound_links = Vec::new();
        
        // Extract page title
        let title_selector = Selector::parse("title").unwrap();
        let page_title = document
            .select(&title_selector)
            .next()
            .map(|el| el.text().collect::<String>())
            .unwrap_or_default();

        // Extract all links
        let link_selector = Selector::parse("a[href]").unwrap();
        
        for element in document.select(&link_selector) {
            if let Some(href) = element.value().attr("href") {
                match Url::parse(href).or_else(|_| Url::parse(url)?.join(href)) {
                    Ok(link_url) => {
                        let link_str = link_url.to_string();
                        
                        // Check if it's an external link (potential backlink)
                        let source_domain = Url::parse(url)?.host_str().unwrap_or("");
                        let target_domain = link_url.host_str().unwrap_or("");
                        
                        if source_domain != target_domain && !target_domain.is_empty() {
                            let anchor_text = element.text().collect::<String>();
                            let context = self.extract_context(&element, &document);
                            let is_nofollow = element.value().attr("rel")
                                .map(|rel| rel.contains("nofollow"))
                                .unwrap_or(false);

                            let backlink = BacklinkData {
                                source_url: url.to_string(),
                                target_url: link_str.clone(),
                                anchor_text,
                                context,
                                page_title: page_title.clone(),
                                domain_authority: 0.0, // TODO: Calculate domain authority
                                is_nofollow,
                                discovered_at: Utc::now(),
                            };
                            
                            backlinks.push(backlink);
                        }
                        
                        // Add to outbound links for further crawling
                        outbound_links.push(link_str);
                    }
                    Err(_) => {
                        debug!("Failed to parse URL: {}", href);
                    }
                }
            }
        }

        Ok((backlinks, outbound_links))
    }

    fn extract_context(&self, element: &scraper::ElementRef, document: &Html) -> String {
        // Extract surrounding text as context
        if let Some(parent) = element.parent() {
            if let Some(parent_element) = parent.value().as_element() {
                let parent_text: String = parent.text().collect();
                // Return first 200 chars as context
                parent_text.chars().take(200).collect()
            } else {
                String::new()
            }
        } else {
            String::new()
        }
    }

    async fn update_seed_urls_from_backlinks(&self, backlinks: &[BacklinkData]) -> Result<()> {
        let mut unique_domains = HashSet::new();
        let mut new_urls = Vec::new();

        for backlink in backlinks {
            if let Ok(url) = Url::parse(&backlink.target_url) {
                if let Some(domain) = url.host_str() {
                    if unique_domains.insert(domain.to_string()) {
                        // This is a new unique domain
                        new_urls.push(backlink.target_url.clone());
                    }
                }
            }
        }

        if !new_urls.is_empty() {
            info!("Adding {} new unique URLs to seed database", new_urls.len());
            self.database.add_seed_urls(&new_urls).await?;
        }

        Ok(())
    }

    pub async fn get_stats(&self) -> Result<(usize, usize)> {
        let visited_count = self.visited_urls.lock().await.len();
        let backlinks_count = self.discovered_backlinks.lock().await.len();
        Ok((visited_count, backlinks_count))
    }
}

impl Clone for BacklinkProcessor {
    fn clone(&self) -> Self {
        Self {
            client: self.client.clone(),
            database: self.database.clone(),
            config: self.config.clone(),
            semaphore: self.semaphore.clone(),
            visited_urls: self.visited_urls.clone(),
            discovered_backlinks: self.discovered_backlinks.clone(),
        }
    }
}

    async fn search_bing_backlinks(&self, target_url: &str) -> Result<Vec<BacklinkData>, CrawlError> {
        let query = format!("linkfromdomain:{}", target_url);
        let search_url = format!(
            "https://www.bing.com/search?q={}&count=50",
            urlencoding::encode(&query)
        );

        let response = self.client.get(&search_url).send().await?;
        let html = response.text().await?;
        let document = Html::parse_document(&html);

        let link_selector = Selector::parse("a[href]").map_err(|_| CrawlError::ParseError("Invalid CSS selector".to_string()))?;
        let mut backlinks = Vec::new();

        for element in document.select(&link_selector) {
            if let Some(href) = element.value().attr("href") {
                if href.starts_with("http") && !href.contains("bing.com") {
                    let backlink = BacklinkData {
                        source_url: href.to_string(),
                        target_url: target_url.to_string(),
                        anchor_text: element.text().collect::<String>(),
                        context: String::new(),
                        page_title: String::new(),
                        domain_authority: 0.0,
                        is_nofollow: false,
                        crawl_date: chrono::Utc::now(),
                    };
                    backlinks.push(backlink);
                }
            }
        }

        Ok(backlinks)
    }

    async fn crawl_page_for_backlinks(&self, page_url: &str, target_url: &str) -> Result<Vec<BacklinkData>, CrawlError> {
        let response = self.client.get(page_url).send().await?;
        let html = response.text().await?;
        let document = Html::parse_document(&html);

        let link_selector = Selector::parse("a[href]").map_err(|_| CrawlError::ParseError("Invalid CSS selector".to_string()))?;
        let mut backlinks = Vec::new();

        for element in document.select(&link_selector) {
            if let Some(href) = element.value().attr("href") {
                if let Ok(absolute_url) = self.resolve_url(page_url, href) {
                    if absolute_url.as_str().contains(target_url) {
                        let anchor_text = element.text().collect::<String>();
                        let context = self.extract_link_context(&element, &document);

                        let backlink = BacklinkData {
                            source_url: page_url.to_string(),
                            target_url: absolute_url.to_string(),
                            anchor_text,
                            context,
                            page_title: self.extract_page_title(&document),
                            domain_authority: 0.0,
                            is_nofollow: element.value().attr("rel")
                                .map(|rel| rel.contains("nofollow"))
                                .unwrap_or(false),
                            crawl_date: chrono::Utc::now(),
                        };
                        backlinks.push(backlink);
                    }
                }
            }
        }

        Ok(backlinks)
    }

    fn resolve_url(&self, base_url: &str, href: &str) -> Result<Url, ParseError> {
        let base = Url::parse(base_url)?;
        base.join(href)
    }

    fn extract_link_context(&self, link_element: &scraper::ElementRef, _document: &Html) -> String {
        // Extract surrounding text context
        let mut context = String::new();

        // Get parent elements for context
        if let Some(parent) = link_element.parent() {
            // Use the parent element's text content
            for text_node in parent.children() {
                if let Some(text) = text_node.value().as_text() {
                    context.push_str(text);
                    context.push(' ');
                }
            }
            // Limit context to reasonable length
            if context.len() > 200 {
                context = context.chars().take(200).collect();
            }
        }

        context.trim().to_string()
    }

    fn extract_page_title(&self, document: &Html) -> String {
        let title_selector = Selector::parse("title").unwrap();
        if let Some(title_element) = document.select(&title_selector).next() {
            title_element.text().collect::<String>().trim().to_string()
        } else {
            String::new()
        }
    }

    pub async fn calculate_domain_authority(&self, backlinks: &[BacklinkData]) -> std::collections::HashMap<String, f64> {
        let mut domain_scores = std::collections::HashMap::new();

        for backlink in backlinks {
            if let Ok(source_domain) = self.extract_domain(&backlink.source_url) {
                let score = domain_scores.entry(source_domain).or_insert(0.0);
                *score += 1.0; // Simple scoring based on backlink count
            }
        }

        // Normalize scores
        let max_score = domain_scores.values().cloned().fold(0.0, f64::max);
        if max_score > 0.0 {
            for score in domain_scores.values_mut() {
                *score = (*score / max_score) * 100.0; // Scale to 0-100
            }
        }

        domain_scores
    }

    fn extract_domain(&self, url: &str) -> Result<String, ParseError> {
        let parsed = Url::parse(url)?;
        Ok(parsed.host_str().unwrap_or("").to_string())
    }

    pub fn detect_spam_backlinks(&self, backlinks: &[BacklinkData]) -> Vec<BacklinkData> {
        let mut spam_backlinks = Vec::new();

        // Simple spam detection heuristics
        let spam_indicators = [
            "casino", "poker", "viagra", "pharmacy", "loan", "insurance",
            "free-money", "make-money-fast", "weight-loss", "dating"
        ];

        for backlink in backlinks {
            let is_spam = spam_indicators.iter().any(|indicator|
                backlink.source_url.to_lowercase().contains(indicator) ||
                backlink.anchor_text.to_lowercase().contains(indicator) ||
                backlink.context.to_lowercase().contains(indicator)
            );

            if is_spam {
                spam_backlinks.push(backlink.clone());
            }
        }

        spam_backlinks
    }
}

pub struct BacklinkAnalyzer {
    processor: BacklinkProcessor,
    database: BacklinkDatabase,
}

impl BacklinkAnalyzer {
    pub fn new(processor: BacklinkProcessor, database: BacklinkDatabase) -> Self {
        Self { processor, database }
    }

    pub async fn analyze_backlinks(&mut self, target_url: &str) -> Result<BacklinkAnalysis, CrawlError> {
        // Discover backlinks
        let backlinks = self.processor.discover_backlinks(target_url).await?;

        // Store backlinks
        self.database.store_backlinks(&backlinks)?;

        // Calculate domain authority
        let domain_scores = self.processor.calculate_domain_authority(&backlinks).await;
        self.database.store_domain_scores(&domain_scores)?;

        // Detect spam backlinks
        let spam_backlinks = self.processor.detect_spam_backlinks(&backlinks);

        // Calculate PageRank (simplified)
        let pagerank_scores = self.calculate_pagerank(&backlinks);
        self.database.store_pagerank_scores(&pagerank_scores)?;

        Ok(BacklinkAnalysis {
            total_backlinks: backlinks.len(),
            unique_domains: domain_scores.len(),
            spam_backlinks: spam_backlinks.len(),
            domain_authority: domain_scores.get(&self.processor.extract_domain(target_url).unwrap_or_default())
                .copied().unwrap_or(0.0),
            pagerank_score: pagerank_scores.get(target_url).copied().unwrap_or(0.0),
        })
    }

    fn calculate_pagerank(&self, backlinks: &[BacklinkData]) -> std::collections::HashMap<String, f64> {
        // Simplified PageRank calculation
        let mut scores = std::collections::HashMap::new();
        let mut outgoing_links = std::collections::HashMap::new();

        // Count outgoing links per domain
        for backlink in backlinks {
            if let Ok(domain) = self.processor.extract_domain(&backlink.source_url) {
                *outgoing_links.entry(domain).or_insert(0) += 1;
            }
        }

        // Calculate PageRank scores
        for backlink in backlinks {
            if let Ok(domain) = self.processor.extract_domain(&backlink.source_url) {
                let outgoing = *outgoing_links.get(&domain).unwrap_or(&1) as f64;
                let score = scores.entry(backlink.target_url.clone()).or_insert(0.0);
                *score += 1.0 / outgoing;
            }
        }

        // Normalize scores
        let max_score = scores.values().cloned().fold(0.0, f64::max);
        if max_score > 0.0 {
            for score in scores.values_mut() {
                *score = (*score / max_score) * 100.0;
            }
        }

        scores
    }
}
