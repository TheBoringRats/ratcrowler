use crate::models::*;
use crate::scheduler::ScheduleManager;
use crate::backlink_processor::BacklinkProcessor;
use crate::database::Database;
use crate::dashboard::DashboardServer;
use crate::crawler::WebsiteCrawler;
use anyhow::Result;
use chrono::Utc;
use log::{info, warn, error};
use std::sync::Arc;
use std::time::Duration;
use tokio::time::{interval, sleep};
use serde_json;

pub struct MainApplication {
    database: Arc<Database>,
    scheduler: ScheduleManager,
    backlink_processor: BacklinkProcessor,
    crawler: WebsiteCrawler,
    dashboard_server: DashboardServer,
    config: MainApplicationConfig,
}

#[derive(Debug, Clone)]
pub struct MainApplicationConfig {
    pub database_path: String,
    pub dashboard_port: u16,
    pub check_interval_minutes: u64,
    pub crawler_config: CrawlerConfig,
    pub web_crawl_config: CrawlConfig,
}

impl Default for MainApplicationConfig {
    fn default() -> Self {
        Self {
            database_path: "ratcrawler.db".to_string(),
            dashboard_port: 8080,
            check_interval_minutes: 10,
            crawler_config: CrawlerConfig::default(),
            web_crawl_config: CrawlConfig::default(),
        }
    }
}

impl MainApplication {
    pub async fn new(config: MainApplicationConfig) -> Result<Self> {
        info!("🚀 Initializing RatCrawler system...");

        // Initialize database
        let database = Arc::new(Database::new(&config.database_path)?);
        info!("✅ Database initialized: {}", config.database_path);

        // Initialize scheduler
        let schedule_config = ScheduleConfig {
            backlink_hours: vec![6, 12, 18, 0], // 4 daily 2-hour sessions
            crawling_hours: (0..24).filter(|h| ![6, 7, 12, 13, 18, 19, 0, 1].contains(h)).collect(),
            timezone: "UTC".to_string(),
            session_duration_hours: 2,
        };
        let scheduler = ScheduleManager::new(schedule_config);
        info!("✅ Scheduler initialized");

        // Initialize backlink processor
        let backlink_processor = BacklinkProcessor::new(database.clone(), config.crawler_config.clone())?;
        info!("✅ Backlink processor initialized");

        // Initialize web crawler
        let crawler = WebsiteCrawler::new(&config.web_crawl_config);
        info!("✅ Web crawler initialized");

        // Initialize dashboard server
        let dashboard_server = DashboardServer::new(database.clone(), config.dashboard_port);
        info!("✅ Dashboard server initialized on port {}", config.dashboard_port);

        Ok(Self {
            database,
            scheduler,
            backlink_processor,
            crawler,
            dashboard_server,
            config,
        })
    }

    pub async fn with_default_config() -> Result<Self> {
        Self::new(MainApplicationConfig::default()).await
    }

    pub async fn start(&mut self) -> Result<()> {
        info!("🕷️  Starting RatCrawler system...");

        // Load seed URLs
        let seed_urls = self.load_initial_seed_urls().await?;
        if seed_urls.is_empty() {
            warn!("⚠️  No seed URLs found. System will wait for URLs to be added.");
        } else {
            info!("📝 Loaded {} seed URLs", seed_urls.len());
        }

        // Start dashboard server in background
        let dashboard_port = self.config.dashboard_port;
        let db_for_dashboard = self.database.clone();
        let dashboard_task = tokio::spawn(async move {
            let mut server = DashboardServer::new(db_for_dashboard, dashboard_port);
            if let Err(e) = server.start().await {
                error!("Dashboard server error: {}", e);
            }
        });

        info!("🌐 Dashboard available at: http://localhost:{}", self.config.dashboard_port);

        // Start main processing loop
        let processing_task = self.start_processing_loop();

        // Wait for both tasks
        tokio::try_join!(
            async { dashboard_task.await.map_err(|e| anyhow::anyhow!("Dashboard task error: {}", e)) },
            processing_task
        )?;

        Ok(())
    }

    pub async fn start_dashboard_only(&mut self) -> Result<()> {
        info!("📊 Starting dashboard-only mode...");

        // Start only the dashboard server
        let db_for_dashboard = Arc::clone(&self.database);
        let dashboard_port = self.config.dashboard_port;

        let dashboard_task = tokio::spawn(async move {
            let server = DashboardServer::new(db_for_dashboard, dashboard_port);
            if let Err(e) = server.start().await {
                error!("Dashboard server error: {}", e);
            }
        });

        info!("🌐 Dashboard available at: http://localhost:{}", self.config.dashboard_port);

        // Wait for dashboard indefinitely
        dashboard_task.await.map_err(|e| anyhow::anyhow!("Dashboard task error: {}", e))?;

        Ok(())
    }

    async fn start_processing_loop(&mut self) -> Result<()> {
        let mut interval = interval(Duration::from_secs(self.config.check_interval_minutes * 60));

        info!("🔄 Starting main processing loop (check every {} minutes)", self.config.check_interval_minutes);

        loop {
            interval.tick().await;

            let current_mode = self.scheduler.get_current_mode().await;

            match current_mode.as_str() {
                "backlink_processing" => {
                    info!("🔗 Entering backlink discovery mode");
                    self.run_backlink_processing().await?;
                }
                "crawling" => {
                    info!("🕸️  Entering web crawling mode");
                    self.run_web_crawling().await?;
                }
                _ => {
                    info!("⏸️  Idle mode - waiting for next scheduled activity");
                    tokio::time::sleep(std::time::Duration::from_secs(60)).await;
                }
            }

            // Update dashboard statistics
            self.update_dashboard_stats().await?;
        }
    }

    async fn run_backlink_processing(&mut self) -> Result<()> {
        info!("🔗 Starting 2-hour backlink processing session...");

        let start_time = Utc::now();
        let backlinks_found = self.backlink_processor.process_backlinks_for_duration(2).await?;
        let end_time = Utc::now();

        info!("✅ Backlink processing completed!");
        info!("   Duration: {} minutes", (end_time - start_time).num_minutes());
        info!("   Backlinks found: {}", backlinks_found);

        // Save processing session info
        self.save_processing_session("backlink_discovery", backlinks_found as i32, None).await?;

        Ok(())
    }

    async fn run_web_crawling(&mut self) -> Result<()> {
        info!("🕸️  Starting web crawling session...");

        let seed_urls = self.database.get_seed_urls(50).await?;
        if seed_urls.is_empty() {
            info!("⏭️  No seed URLs available, skipping crawling session");
            return Ok(());
        }

        let urls: Vec<String> = seed_urls.iter().map(|s| s.url.clone()).collect();
        info!("📝 Crawling {} URLs", urls.len());

        let start_time = Utc::now();
        let result = self.crawler.crawl(urls, &self.database).await?;
        let end_time = Utc::now();

        info!("✅ Web crawling completed!");
        info!("   Duration: {} minutes", (end_time - start_time).num_minutes());
        info!("   Pages crawled: {}", result.pages_crawled.unwrap_or(0));
        info!("   Errors: {}", result.errors.unwrap_or(0));

        // Save processing session info
        self.save_processing_session("web_crawling", result.pages_crawled.unwrap_or(0) as i32, result.errors).await?;

        Ok(())
    }

    async fn save_processing_session(&self, session_type: &str, items_processed: i32, errors: Option<usize>) -> Result<()> {
        // TODO: Implement session logging in database
        info!("💾 Session saved: {} processed {} items", session_type, items_processed);
        Ok(())
    }

    async fn load_initial_seed_urls(&self) -> Result<Vec<SeedUrl>> {
        // Try to load from database first
        let db_seeds = self.database.get_seed_urls(1000).await?;
        if !db_seeds.is_empty() {
            return Ok(db_seeds);
        }

        // If database is empty, try to load from seed_urls.json
        if let Ok(content) = tokio::fs::read_to_string("seed_urls.json").await {
            if let Ok(urls) = serde_json::from_str::<Vec<String>>(&content) {
                info!("📂 Loading {} seed URLs from seed_urls.json", urls.len());
                self.database.add_seed_urls(&urls).await?;
                return self.database.get_seed_urls(1000).await;
            }
        }

        // Return empty vec if no seeds found
        Ok(Vec::new())
    }

    async fn update_dashboard_stats(&self) -> Result<()> {
        let current_mode = self.scheduler.get_current_mode().await;
        let next_switch = Utc::now(); // TODO: Implement next_mode_switch_time

        let stats = DashboardStats {
            total_urls_crawled: 0, // TODO: Get from database
            total_backlinks_found: 0, // TODO: Get from database
            unique_domains: 0, // TODO: Get from database
            crawl_rate_per_hour: 0.0,
            backlink_rate_per_hour: 0.0,
            database_size_mb: 0.0,
            system_memory_usage: 0.0,
            system_cpu_usage: 0.0,
            current_mode,
            next_mode_switch: next_switch,
            last_updated: Utc::now(),
        };

        // TODO: Update dashboard with stats
        Ok(())
    }
}
