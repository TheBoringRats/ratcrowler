mod models;
mod scheduler;
mod dashboard;

use anyhow::Result;
use chrono::Utc;
use log::{info, error};
use std::sync::Arc;
use tokio::signal;
use tracing_subscriber;

// Import the new modules
include!("database_new.rs");
include!("crawler_new.rs");

use crate::database::Database;
use crate::crawler_new::Crawler;
use crate::backlink_processor::BacklinkProcessor;
use crate::scheduler::ScheduleManager;
use crate::dashboard::DashboardServer;
use crate::models::{CrawlerConfig, ScheduleConfig};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();
    env_logger::init();

    info!("Starting RatCrawler Rust Version...");

    // Initialize database
    let db_path = "ratcrawler.db";
    let database = Arc::new(Database::new(db_path)?);
    info!("Database initialized");

    // Initialize seed URLs from JSON file
    initialize_seed_urls(&database).await?;

    // Create configurations
    let crawler_config = CrawlerConfig::default();
    let schedule_config = ScheduleConfig::default();

    // Initialize components
    let crawler = Arc::new(Crawler::new(database.clone(), crawler_config.clone())?);
    let backlink_processor = Arc::new(BacklinkProcessor::new(database.clone(), crawler_config)?);
    let schedule_manager = Arc::new(ScheduleManager::new(schedule_config));

    // Start dashboard server
    let dashboard_server = DashboardServer::new(database.clone(), 8080);
    let dashboard_handle = {
        let server = dashboard_server;
        tokio::spawn(async move {
            if let Err(e) = server.start().await {
                error!("Dashboard server error: {}", e);
            }
        })
    };

    // Start main processing loop
    let processing_handle = {
        let crawler = crawler.clone();
        let backlink_processor = backlink_processor.clone();
        let schedule_manager = schedule_manager.clone();
        let database = database.clone();

        tokio::spawn(async move {
            loop {
                let current_mode = schedule_manager.get_current_mode().await;

                match current_mode.as_str() {
                    "backlink_processing" => {
                        info!("Starting backlink processing mode for 2 hours");
                        match backlink_processor.process_backlinks_for_duration(2).await {
                            Ok(count) => info!("Backlink processing completed. Found {} backlinks", count),
                            Err(e) => error!("Backlink processing failed: {}", e),
                        }
                    }
                    "crawling" => {
                        info!("Starting crawling mode");
                        // Calculate hours until next backlink processing
                        let next_switch = schedule_manager.get_next_mode_switch().await;
                        let hours_until_switch = (next_switch - Utc::now()).num_hours().max(1) as u64;

                        match crawler.crawl_for_duration(hours_until_switch).await {
                            Ok(count) => info!("Crawling completed. Crawled {} URLs", count),
                            Err(e) => error!("Crawling failed: {}", e),
                        }
                    }
                    "idle" => {
                        info!("System in idle mode, waiting 60 seconds");
                        tokio::time::sleep(tokio::time::Duration::from_secs(60)).await;
                    }
                    _ => {
                        error!("Unknown mode: {}", current_mode);
                        tokio::time::sleep(tokio::time::Duration::from_secs(60)).await;
                    }
                }

                // Update database stats
                if let Ok(stats) = database.get_dashboard_stats().await {
                    if let Err(e) = database.update_stats(&stats).await {
                        error!("Failed to update stats: {}", e);
                    }
                }

                // Small delay before checking mode again
                tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
            }
        })
    };

    // Start scheduler
    let scheduler_handle = {
        let schedule_manager = schedule_manager.clone();
        tokio::spawn(async move {
            if let Err(e) = schedule_manager.start().await {
                error!("Scheduler error: {}", e);
            }
        })
    };

    info!("All services started successfully!");
    info!("Dashboard available at: http://localhost:8080");

    // Wait for shutdown signal
    signal::ctrl_c().await?;
    info!("Shutdown signal received");

    // Cancel all tasks
    dashboard_handle.abort();
    processing_handle.abort();
    scheduler_handle.abort();

    info!("RatCrawler shutdown complete");
    Ok(())
}

async fn initialize_seed_urls(database: &Arc<Database>) -> Result<()> {
    info!("Initializing seed URLs from seed_urls.json");

    // Read seed URLs from JSON file
    let seed_file = std::fs::read_to_string("../../seed_urls.json")
        .or_else(|_| std::fs::read_to_string("seed_urls.json"))
        .unwrap_or_else(|_| {
            // Default seed URLs if file not found
            serde_json::to_string(&vec![
                "https://github.com",
                "https://stackoverflow.com",
                "https://wikipedia.org",
                "https://python.org",
                "https://www.google.com",
                "https://www.youtube.com",
                "https://www.microsoft.com",
                "https://developer.mozilla.org",
                "https://www.w3schools.com",
                "https://www.freecodecamp.org",
                "https://leetcode.com",
                "https://www.reddit.com",
                "https://medium.com"
            ]).unwrap_or_default()
        });

    let seed_urls: Vec<String> = serde_json::from_str(&seed_file)
        .unwrap_or_else(|e| {
            error!("Failed to parse seed URLs: {}", e);
            vec![
                "https://github.com".to_string(),
                "https://stackoverflow.com".to_string(),
                "https://wikipedia.org".to_string(),
            ]
        });

    database.add_seed_urls(&seed_urls).await?;
    info!("Added {} seed URLs to database", seed_urls.len());

    Ok(())
}
