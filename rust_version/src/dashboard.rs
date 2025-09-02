use crate::database::Database;
use crate::models::{DashboardStats, SystemHealth};
use anyhow::Result;
use log::{info, error};
use serde_json::json;
use std::convert::Infallible;
use std::sync::Arc;
use sysinfo::{System, SystemExt, CpuExt};
use warp::{Filter, Reply};

pub struct DashboardServer {
    database: Arc<Database>,
    port: u16,
}

impl DashboardServer {
    pub fn new(database: Arc<Database>, port: u16) -> Self {
        Self { database, port }
    }

    pub async fn start(&self) -> Result<()> {
        info!("Starting dashboard server on port {}", self.port);

        let db = self.database.clone();

        // Route for serving the main dashboard HTML
        let dashboard_route = warp::path::end()
            .map(|| {
                warp::reply::html(include_str!("../templates/dashboard.html"))
            });

        // API route for dashboard stats
        let stats_route = warp::path("api")
            .and(warp::path("stats"))
            .and(warp::path::end())
            .and(with_db(db.clone()))
            .and_then(get_dashboard_stats);

        // API route for recent crawls
        let crawls_route = warp::path("api")
            .and(warp::path("recent-crawls"))
            .and(warp::path::end())
            .and(with_db(db.clone()))
            .and_then(get_recent_crawls);

        // Static files route
        let static_route = warp::path("static")
            .and(warp::fs::dir("static"));

        // Health check route
        let health_route = warp::path("health")
            .and(warp::path::end())
            .map(|| {
                warp::reply::json(&json!({
                    "status": "healthy",
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }))
            });

        let routes = dashboard_route
            .or(stats_route)
            .or(crawls_route)
            .or(static_route)
            .or(health_route)
            .with(warp::cors().allow_any_origin());

        warp::serve(routes)
            .run(([0, 0, 0, 0], self.port))
            .await;

        Ok(())
    }
}

fn with_db(db: Arc<Database>) -> impl Filter<Extract = (Arc<Database>,), Error = Infallible> + Clone {
    warp::any().map(move || db.clone())
}

async fn get_dashboard_stats(db: Arc<Database>) -> Result<impl Reply, Infallible> {
    match db.get_dashboard_stats().await {
        Ok(mut stats) => {
            // Update system stats
            let mut system = System::new_all();
            system.refresh_all();

            stats.system_memory_usage = (system.used_memory() as f64 / system.total_memory() as f64) * 100.0;
            stats.system_cpu_usage = system.global_cpu_info().cpu_usage() as f64;

            Ok(warp::reply::json(&stats))
        }
        Err(e) => {
            error!("Failed to get dashboard stats: {}", e);
            Ok(warp::reply::json(&json!({
                "error": "Failed to get stats"
            })))
        }
    }
}

async fn get_recent_crawls(db: Arc<Database>) -> Result<impl Reply, Infallible> {
    match db.get_recent_crawls(50).await {
        Ok(crawls) => Ok(warp::reply::json(&crawls)),
        Err(e) => {
            error!("Failed to get recent crawls: {}", e);
            Ok(warp::reply::json(&json!({
                "error": "Failed to get recent crawls"
            })))
        }
    }
}
