use reqwest::Client;
use scraper::{Html, Selector};
use std::collections::HashSet;
use std::time::Duration;
use url::{Url, ParseError};
use crate::models::*;
use crate::database::BacklinkDatabase;
use regex::Regex;

pub struct BacklinkProcessor {
    client: Client,
    user_agent: String,
    timeout: Duration,
    max_redirects: usize,
}

impl BacklinkProcessor {
    pub fn new(user_agent: String, timeout_secs: u64, max_redirects: usize) -> Self {
        let client = Client::builder()
            .user_agent(&user_agent)
            .timeout(Duration::from_secs(timeout_secs))
            .redirect(reqwest::redirect::Policy::limited(max_redirects))
            .build()
            .expect("Failed to build HTTP client");

        Self {
            client,
            user_agent,
            timeout: Duration::from_secs(timeout_secs),
            max_redirects,
        }
    }

    pub async fn discover_backlinks(&self, target_url: &str) -> Result<Vec<BacklinkData>, CrawlError> {
        let mut backlinks = Vec::new();
        let mut visited_urls = HashSet::new();
        let mut urls_to_check = vec![target_url.to_string()];

        // Get referring domains from search engines and other sources
        let search_backlinks = self.get_search_engine_backlinks(target_url).await?;
        backlinks.extend(search_backlinks);

        // Crawl for backlinks from discovered pages
        while let Some(url) = urls_to_check.pop() {
            if visited_urls.contains(&url) || visited_urls.len() >= 1000 {
                continue;
            }

            visited_urls.insert(url.clone());

            match self.crawl_page_for_backlinks(&url, target_url).await {
                Ok(page_backlinks) => {
                    for backlink in page_backlinks {
                        if !backlinks.iter().any(|b| b.source_url == backlink.source_url) {
                            backlinks.push(backlink);
                        }
                    }
                }
                Err(_) => continue, // Skip pages that can't be crawled
            }
        }

        Ok(backlinks)
    }

    async fn get_search_engine_backlinks(&self, target_url: &str) -> Result<Vec<BacklinkData>, CrawlError> {
        let mut backlinks = Vec::new();

        // Google search for backlinks
        if let Ok(google_links) = self.search_google_backlinks(target_url).await {
            backlinks.extend(google_links);
        }

        // Bing search for backlinks
        if let Ok(bing_links) = self.search_bing_backlinks(target_url).await {
            backlinks.extend(bing_links);
        }

        Ok(backlinks)
    }

    async fn search_google_backlinks(&self, target_url: &str) -> Result<Vec<BacklinkData>, CrawlError> {
        let query = format!("link:{}", target_url);
        let search_url = format!(
            "https://www.google.com/search?q={}&num=100",
            urlencoding::encode(&query)
        );

        let response = self.client.get(&search_url).send().await?;
        let html = response.text().await?;
        let document = Html::parse_document(&html);

        let link_selector = Selector::parse("a[href]").map_err(|_| CrawlError::ParseError("Invalid CSS selector".to_string()))?;
        let mut backlinks = Vec::new();

        for element in document.select(&link_selector) {
            if let Some(href) = element.value().attr("href") {
                if href.starts_with("http") && !href.contains("google.com") {
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
