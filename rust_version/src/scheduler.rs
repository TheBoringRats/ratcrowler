use crate::models::{ScheduleConfig, SystemHealth};
use chrono::{DateTime, Utc, Timelike};
use log::{info, warn, error};
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::time::{sleep, Duration};

pub struct ScheduleManager {
    config: ScheduleConfig,
    current_mode: Arc<RwLock<String>>,
    system_start_time: DateTime<Utc>,
}

impl ScheduleManager {
    pub fn new(config: ScheduleConfig) -> Self {
        Self {
            config,
            current_mode: Arc::new(RwLock::new("idle".to_string())),
            system_start_time: Utc::now(),
        }
    }

    pub async fn start(&self) -> anyhow::Result<()> {
        info!("Starting schedule manager with config: {:?}", self.config);

        loop {
            let current_time = Utc::now();
            let current_hour = current_time.hour();

            let should_process_backlinks = self.config.backlink_hours.contains(&current_hour);
            let should_crawl = self.config.crawling_hours.contains(&current_hour);

            let new_mode = if should_process_backlinks {
                "backlink_processing"
            } else if should_crawl {
                "crawling"
            } else {
                "idle"
            };

            let mut current_mode = self.current_mode.write().await;
            if *current_mode != new_mode {
                info!("Switching mode from {} to {}", *current_mode, new_mode);
                *current_mode = new_mode.to_string();
            }
            drop(current_mode);

            // Check every minute
            sleep(Duration::from_secs(60)).await;
        }
    }

    pub async fn get_current_mode(&self) -> String {
        self.current_mode.read().await.clone()
    }

    pub async fn get_next_mode_switch(&self) -> DateTime<Utc> {
        let current_time = Utc::now();
        let current_hour = current_time.hour();

        // Find the next scheduled hour
        let mut next_hour = None;
        for hour in &self.config.backlink_hours {
            if *hour > current_hour {
                next_hour = Some(*hour);
                break;
            }
        }

        if next_hour.is_none() {
            for hour in &self.config.crawling_hours {
                if *hour > current_hour {
                    next_hour = Some(*hour);
                    break;
                }
            }
        }

        // If no hour found today, use first hour of tomorrow
        let target_hour = next_hour.unwrap_or(
            self.config.backlink_hours.iter()
                .chain(self.config.crawling_hours.iter())
                .min()
                .copied()
                .unwrap_or(0)
        );

        let mut next_switch = current_time
            .with_hour(target_hour)
            .unwrap()
            .with_minute(0)
            .unwrap()
            .with_second(0)
            .unwrap()
            .with_nanosecond(0)
            .unwrap();

        if next_switch <= current_time {
            next_switch = next_switch + chrono::Duration::days(1);
        }

        next_switch
    }

    pub async fn get_system_health(&self) -> SystemHealth {
        let uptime = (Utc::now() - self.system_start_time).num_seconds() as u64;

        SystemHealth {
            database_status: "healthy".to_string(),
            crawler_status: "running".to_string(),
            backlink_processor_status: "running".to_string(),
            scheduler_status: "running".to_string(),
            uptime_seconds: uptime,
            errors_last_hour: 0, // TODO: Implement error counting
            warnings_last_hour: 0, // TODO: Implement warning counting
        }
    }

    pub fn is_backlink_processing_time(&self) -> bool {
        let current_hour = Utc::now().hour();
        self.config.backlink_hours.contains(&current_hour)
    }

    pub fn is_crawling_time(&self) -> bool {
        let current_hour = Utc::now().hour();
        self.config.crawling_hours.contains(&current_hour)
    }
}
