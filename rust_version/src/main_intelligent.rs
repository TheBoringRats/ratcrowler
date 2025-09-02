use std::env;
use log::info;

mod models;
mod database;
mod backlink_processor;
mod crawler;
mod scheduler;
mod dashboard;
mod main_app;

use models::{CrawlerConfig, CrawlConfig};
use main_app::{MainApplication, MainApplicationConfig};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    env_logger::init();

    println!("🕷️  RatCrawler - Intelligent Web Crawling & Backlink Discovery System");
    println!("=================================================================");
    println!("🔄 Schedule: 2-hour backlink discovery sessions + web crawling");
    println!("🌐 Dashboard: http://localhost:8080");
    println!("📊 Real-time progress monitoring available");
    println!("");

    let args: Vec<String> = env::args().collect();

    if args.len() > 1 && args[1] == "--daemon" {
        // Run as a daemon with the intelligent scheduling system
        run_intelligent_crawler().await?;
    } else {
        // Show help and available commands
        show_help();
    }

    Ok(())
}

async fn run_intelligent_crawler() -> Result<(), Box<dyn std::error::Error>> {
    info!("🚀 Starting RatCrawler intelligent scheduling system");

    let config = MainApplicationConfig {
        database_path: "ratcrawler_production.db".to_string(),
        dashboard_port: 8080,
        check_interval_minutes: 5, // Check every 5 minutes
        crawler_config: CrawlerConfig {
            max_concurrent_requests: 20,
            delay_between_requests_ms: 500,
            request_timeout_seconds: 30,
            max_retries: 3,
            respect_robots_txt: true,
            user_agents: vec![
                "RatCrawler/2.0 (Intelligent Web Crawler)".to_string(),
                "Mozilla/5.0 (compatible; RatCrawler/2.0; +http://ratcrawler.io/bot)".to_string(),
            ],
            max_depth: 5,
            enable_javascript: false,
        },
        web_crawl_config: CrawlConfig {
            user_agent: "RatCrawler/2.0 (Intelligent Web Crawler)".to_string(),
            timeout_secs: 30,
            max_redirects: 5,
            max_depth: 5,
            max_pages: 1000,
            delay_ms: 500,
            respect_robots_txt: true,
        },
    };

    let mut app = MainApplication::new(config).await?;

    info!("🎯 System configured for intelligent processing:");
    info!("   • 4x daily 2-hour backlink discovery sessions");
    info!("   • Continuous web crawling between sessions");
    info!("   • Automatic seed URL updates from unique discoveries");
    info!("   • Real-time dashboard monitoring");

    app.start().await?;

    Ok(())
}

fn show_help() {
    println!("Available Commands:");
    println!("  ratcrawler --daemon              - Start intelligent crawler daemon");
    println!("  ratcrawler                      - Show this help");
    println!("");
    println!("🤖 Intelligent Daemon Mode:");
    println!("  • Alternates between 2-hour backlink discovery and web crawling");
    println!("  • Automatically updates seed URLs when unique domains found");
    println!("  • Real-time dashboard at http://localhost:8080");
    println!("  • Respects robots.txt and implements smart delays");
    println!("  • Comprehensive logging and monitoring");
    println!("");
    println!("📈 Schedule Overview:");
    println!("  06:00-08:00  Backlink Discovery Session #1");
    println!("  08:00-12:00  Web Crawling");
    println!("  12:00-14:00  Backlink Discovery Session #2");
    println!("  14:00-18:00  Web Crawling");
    println!("  18:00-20:00  Backlink Discovery Session #3");
    println!("  20:00-00:00  Web Crawling");
    println!("  00:00-02:00  Backlink Discovery Session #4");
    println!("  02:00-06:00  Web Crawling");
    println!("");
    println!("🌟 Features:");
    println!("  • Concurrent processing with configurable limits");
    println!("  • Automatic duplicate detection and filtering");
    println!("  • Real-time progress monitoring and statistics");
    println!("  • SQLite database with comprehensive indexing");
    println!("  • Responsive web dashboard with live updates");
    println!("  • Intelligent seed URL management and expansion");
    println!("");
    println!("Get started: ratcrawler --daemon");
}
