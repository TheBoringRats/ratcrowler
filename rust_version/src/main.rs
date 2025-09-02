use anyhow::Result;
use clap::{Arg, Command};
use log::info;

mod models;
mod database;
mod backlink_processor;
mod crawler;
mod scheduler;
mod dashboard;
mod main_app;

use main_app::MainApplication;

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();

    let matches = Command::new("ratcrawler")
        .version("1.0.0")
        .author("Swadhin")
        .about("Intelligent Web Crawler with Scheduling and Backlink Processing")
        .arg(
            Arg::new("daemon")
                .long("daemon")
                .help("Run as intelligent daemon with automatic scheduling")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("dashboard-only")
                .long("dashboard-only")
                .help("Run only the dashboard server")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("config")
                .long("config")
                .value_name("FILE")
                .help("Sets a custom config file")
                .default_value("config.json"),
        )
        .get_matches();

    info!("� Starting RatCrawler Intelligent System");

    if matches.get_flag("daemon") {
        info!("🤖 Running in intelligent daemon mode");
        info!("📅 Schedule: 4x daily 2-hour backlink sessions (06:00-08:00, 12:00-14:00, 18:00-20:00, 00:00-02:00)");
        info!("🕷️  Continuous crawling between backlink sessions");
        info!("🌐 Dashboard available at: http://localhost:8080");

        let mut app = MainApplication::with_default_config().await?;
        app.start().await?;
    } else if matches.get_flag("dashboard-only") {
        info!("📊 Running dashboard-only mode");
        info!("🌐 Dashboard available at: http://localhost:8080");

        let mut app = MainApplication::with_default_config().await?;
        app.start_dashboard_only().await?;
    } else {
        // Show help by default
        let mut cmd = Command::new("ratcrawler")
            .version("1.0.0")
            .author("Swadhin")
            .about("Intelligent Web Crawler with Scheduling and Backlink Processing")
            .arg(
                Arg::new("daemon")
                    .long("daemon")
                    .help("Run as intelligent daemon with automatic scheduling")
                    .action(clap::ArgAction::SetTrue),
            )
            .arg(
                Arg::new("dashboard-only")
                    .long("dashboard-only")
                    .help("Run only the dashboard server")
                    .action(clap::ArgAction::SetTrue),
            );

        cmd.print_help()?;
        println!("\n\n🚀 Welcome to RatCrawler Intelligent System!");
        println!("📅 Features:");
        println!("   • Intelligent scheduling with 4x daily 2-hour backlink sessions");
        println!("   • Automatic seed URL updates when unique domains found");
        println!("   • Beautiful real-time dashboard for monitoring");
        println!("   • Concurrent processing with smart delays");
        println!("\n💡 Usage:");
        println!("   cargo run -- --daemon          # Start intelligent daemon");
        println!("   cargo run -- --dashboard-only  # Dashboard only");
        println!("\n🌐 Dashboard: http://localhost:8080");
    }
    Ok(())
}
