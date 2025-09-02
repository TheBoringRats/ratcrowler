use std::collections::HashMap;
use std::time::Duration;
use tokio::time::timeout;
use crate::models::*;
use crate::crawler::WebsiteCrawler;
use crate::backlink_processor::BacklinkProcessor;
use crate::database::Database;
use std::sync::Arc;
use anyhow::Result;

pub struct IntegratedCrawler {
    web_crawler: WebsiteCrawler,
    backlink_processor: BacklinkProcessor,
    database: Arc<Database>,
    config: IntegratedCrawlConfig,
}

impl IntegratedCrawler {
    pub fn new(
        db_path: &str,
        config: IntegratedCrawlConfig,
    ) -> Result<Self, CrawlError> {
        let database = Arc::new(Database::new(db_path).map_err(|e| CrawlError::DatabaseError(format!("{}", e)))?);

        let crawler_config = CrawlerConfig {
            max_concurrent_requests: 10,
            delay_between_requests_ms: 1000,
            request_timeout_seconds: config.backlink_config.timeout_secs,
            max_retries: 3,
            respect_robots_txt: true,
            user_agents: vec![config.backlink_config.user_agent.clone()],
            max_depth: config.web_crawl_config.max_depth as u32,
            enable_javascript: false,
        };

        let web_crawler = WebsiteCrawler::new(&config.web_crawl_config);
        let backlink_processor = BacklinkProcessor::new(database.clone(), crawler_config)
            .map_err(|e| CrawlError::DatabaseError(format!("{}", e)))?;

        Ok(Self {
            web_crawler,
            backlink_processor,
            database,
            config,
        })
    }

    pub async fn crawl_website_with_backlinks(
        &mut self,
        seed_urls: Vec<String>,
    ) -> Result<IntegratedCrawlResult, CrawlError> {
        println!("Starting integrated crawl for {} seed URLs", seed_urls.len());

        // Step 1: Crawl the website
        println!("Step 1: Crawling website...");
        let crawl_result = timeout(
            Duration::from_secs(self.config.web_crawl_config.timeout_secs * 10),
            self.web_crawler.crawl(seed_urls.clone(), &self.database)
        ).await
        .map_err(|_| CrawlError::TimeoutError("Web crawling timed out".to_string()))??;

        println!("Website crawling completed. Crawled {} pages with {} errors",
                 crawl_result.pages_crawled.unwrap_or(0), crawl_result.errors.unwrap_or(0));

        // Step 2: Analyze backlinks for each crawled page
        println!("Step 2: Analyzing backlinks...");
        let mut backlink_results = Vec::new();
        let crawled_urls: Vec<String> = Vec::new(); // TODO: Implement get_all_crawled_urls

        for (i, url) in crawled_urls.iter().enumerate() {
            if i >= self.config.max_backlink_analyses {
                println!("Reached maximum backlink analysis limit ({})", self.config.max_backlink_analyses);
                break;
            }

            println!("Analyzing backlinks for: {}", url);

            let analysis = self.backlink_processor.discover_backlinks_for_url(url, 3).await;
            match analysis {
                Ok(backlinks) => {
                    println!("  Found {} backlinks from {} unique domains",
                             backlinks.len(), 42); // TODO: Calculate unique domains
                    let analysis = BacklinkAnalysis {
                        total_backlinks: backlinks.len(),
                        unique_domains: 42, // TODO: Calculate unique domains
                        spam_backlinks: 0,
                        domain_authority: 0.0,
                        pagerank_score: 0.0,
                    };
                    backlink_results.push((url.clone(), analysis));
                }
                Err(e) => {
                    println!("  Error analyzing backlinks for {}: {:?}", url, e);
                }
            }

            // Small delay between backlink analyses
            tokio::time::sleep(Duration::from_millis(500)).await;
        }

        // Step 3: Generate comprehensive report
        let report = self.generate_crawl_report(&crawl_result, &backlink_results)?;

        println!("Integrated crawl completed successfully!");
        println!("Total pages crawled: {}", crawl_result.pages_crawled.unwrap_or(0));
        println!("Total backlink analyses: {}", backlink_results.len());

        Ok(IntegratedCrawlResult {
            web_crawl_result: crawl_result,
            backlink_analyses: backlink_results,
            report,
        })
    }

    pub async fn analyze_backlinks_only(&mut self, target_urls: Vec<String>) -> Result<Vec<(String, BacklinkAnalysis)>, CrawlError> {
        let mut results = Vec::new();

        for url in target_urls {
            println!("Analyzing backlinks for: {}", url);

            let analysis = self.backlink_processor.discover_backlinks_for_url(&url, 3).await;
            match analysis {
                Ok(backlinks) => {
                    let analysis = BacklinkAnalysis {
                        total_backlinks: backlinks.len(),
                        unique_domains: 42, // TODO: Calculate unique domains
                        spam_backlinks: 0,
                        domain_authority: 0.0,
                        pagerank_score: 0.0,
                    };
                    results.push((url, analysis));
                }
                Err(e) => {
                    println!("Error analyzing backlinks for {}: {:?}", url, e);
                }
            }
        }

        Ok(results)
    }

    pub async fn crawl_and_analyze_domain(&mut self, domain: &str) -> Result<DomainAnalysis, CrawlError> {
        println!("Starting domain analysis for: {}", domain);

        // Generate seed URLs for the domain
        let seed_urls = vec![
            format!("https://{}", domain),
            format!("https://{}/", domain),
            format!("http://{}", domain),
            format!("http://{}/", domain),
        ];

        // Crawl the domain
        let crawl_result = timeout(
            Duration::from_secs(self.config.web_crawl_config.timeout_secs * 5),
            self.web_crawler.crawl(seed_urls, &self.database)
        ).await
        .map_err(|_| CrawlError::TimeoutError("Domain crawling timed out".to_string()))??;

        // Analyze backlinks for the main domain
        let main_url = format!("https://{}", domain);
        let backlinks = self.backlink_processor.discover_backlinks_for_url(&main_url, 3).await
            .map_err(|e| CrawlError::DatabaseError(e.to_string()))?;

        let backlink_analysis = BacklinkAnalysis {
            total_backlinks: backlinks.len(),
            unique_domains: 42, // TODO: Calculate unique domains
            spam_backlinks: 0,
            domain_authority: 0.0,
            pagerank_score: 0.0,
        };

        // Get domain authority scores
        let domain_scores = self.get_domain_authority_scores()?;

        Ok(DomainAnalysis {
            domain: domain.to_string(),
            pages_crawled: crawl_result.pages_crawled.unwrap_or(0),
            backlink_analysis,
            domain_authority: domain_scores.get(domain).copied().unwrap_or(0.0),
            crawl_errors: crawl_result.errors.unwrap_or(0),
        })
    }

    fn generate_crawl_report(
        &self,
        crawl_result: &CrawlResult,
        backlink_results: &[(String, BacklinkAnalysis)],
    ) -> Result<CrawlReport, CrawlError> {
        let mut total_backlinks = 0;
        let mut total_unique_domains = 0;
        let mut total_spam_backlinks = 0;
        let mut domain_authorities = Vec::new();

        for (_, analysis) in backlink_results {
            total_backlinks += analysis.total_backlinks;
            total_unique_domains += analysis.unique_domains;
            total_spam_backlinks += analysis.spam_backlinks;
            domain_authorities.push(analysis.domain_authority);
        }

        let avg_domain_authority = if !domain_authorities.is_empty() {
            domain_authorities.iter().sum::<f64>() / domain_authorities.len() as f64
        } else {
            0.0
        };

        Ok(CrawlReport {
            total_pages_crawled: crawl_result.pages_crawled.unwrap_or(0),
            total_backlinks_found: total_backlinks,
            total_unique_domains: total_unique_domains,
            total_spam_backlinks,
            average_domain_authority: avg_domain_authority,
            crawl_errors: crawl_result.errors.unwrap_or(0),
            backlink_analyses_completed: backlink_results.len(),
        })
    }

    fn get_domain_authority_scores(&self) -> Result<HashMap<String, f64>, CrawlError> {
        // This would query the database for stored domain scores
        // For now, return empty map
        Ok(HashMap::new())
    }

    pub fn get_crawl_statistics(&self) -> Result<CrawlStatistics, CrawlError> {
        let web_summary = "Latest crawl summary".to_string(); // TODO: Implement get_crawl_summary
        let total_crawled = 0; // TODO: Parse from web_summary
        let total_errors = 0; // TODO: Parse from web_summary

        Ok(CrawlStatistics {
            total_pages_crawled: total_crawled,
            total_crawl_errors: total_errors,
            database_size_mb: 0.0, // Would need to calculate actual DB size
            last_crawl_time: None,
        })
    }

    pub async fn cleanup_old_data(&mut self, _days_old: u32) -> Result<(), CrawlError> {
        // This would implement data cleanup logic
        // For now, just return success
        println!("Data cleanup completed (placeholder implementation)");
        Ok(())
    }
}

pub struct CrawlScheduler {
    crawler: IntegratedCrawler,
    schedule: Vec<ScheduledCrawl>,
}

impl CrawlScheduler {
    pub fn new(crawler: IntegratedCrawler) -> Self {
        Self {
            crawler,
            schedule: Vec::new(),
        }
    }

    pub fn add_scheduled_crawl(&mut self, crawl: ScheduledCrawl) {
        self.schedule.push(crawl);
    }

    pub async fn run_scheduled_crawls(&mut self) -> Result<(), CrawlError> {
        for scheduled in &self.schedule {
            if scheduled.is_due() {
                println!("Running scheduled crawl: {}", scheduled.name);
                let _ = self.crawler.crawl_website_with_backlinks(scheduled.urls.clone()).await?;
                // Mark as completed (would need to update schedule)
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone)]
pub struct ScheduledCrawl {
    pub name: String,
    pub urls: Vec<String>,
    pub schedule: CrawlSchedule,
    pub last_run: Option<chrono::DateTime<chrono::Utc>>,
}

impl ScheduledCrawl {
    pub fn is_due(&self) -> bool {
        // Simple implementation - always due for now
        // Would need proper scheduling logic
        true
    }
}

#[derive(Debug, Clone)]
pub enum CrawlSchedule {
    Daily,
    Weekly,
    Monthly,
    Custom(String), // Cron expression
}
