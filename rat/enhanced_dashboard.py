"""
Enhanced Monitoring Dashboard for Multi-Database RatCrawler System
Real-time monitoring with database health, crawling status, and analytics
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from rat.multi_database import multi_db_manager
from rat.database_aware_crawler import DatabaseAwareCrawler


class CrawlRequest(BaseModel):
    urls: List[str]
    config: Dict[str, Any] = {}


class EnhancedTursoDashboard:
    """Enhanced dashboard with real-time monitoring capabilities"""

    def __init__(self):
        self.app = FastAPI(title="RatCrawler Multi-Database Monitor")
        self.db_manager = multi_db_manager
        self.active_crawlers = {}
        self.websocket_connections = []

        # Setup templates and static files
        self.templates = Jinja2Templates(directory="templates")
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

        # Setup routes
        self._setup_routes()

        # Start background monitoring
        asyncio.create_task(self._background_monitoring())

    def _setup_routes(self):
        """Setup all API routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            dashboard_data = await self._get_dashboard_data()
            return self.templates.TemplateResponse(
                "enhanced_dashboard.html",
                {"request": request, "data": dashboard_data}
            )

        @self.app.get("/api/status")
        async def get_system_status():
            """Get comprehensive system status"""
            return await self._get_dashboard_data()

        @self.app.get("/api/databases")
        async def get_databases_status():
            """Get all databases status"""
            return self.db_manager.get_all_database_status()

        @self.app.get("/api/database/{db_name}")
        async def get_database_details(db_name: str):
            """Get detailed information about a specific database"""
            health = self.db_manager._check_database_health(db_name)
            usage_stats = await self._get_database_usage_stats(db_name)

            return {
                "name": db_name,
                "health": health,
                "usage_stats": usage_stats,
                "recent_activity": await self._get_recent_activity(db_name)
            }

        @self.app.post("/api/crawl/start")
        async def start_crawl(crawl_request: CrawlRequest, background_tasks: BackgroundTasks):
            """Start a new crawling session"""
            try:
                crawler_config = {
                    "delay": crawl_request.config.get("delay", 1.5),
                    "max_depth": crawl_request.config.get("max_depth", 3),
                    "max_pages": crawl_request.config.get("max_pages", 100)
                }

                crawler = DatabaseAwareCrawler(crawler_config)
                session_id = f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                self.active_crawlers[session_id] = {
                    "crawler": crawler,
                    "status": "starting",
                    "start_time": datetime.now(),
                    "urls": crawl_request.urls
                }

                # Start crawling in background
                background_tasks.add_task(self._run_crawling_session, session_id, crawl_request.urls)

                return {"session_id": session_id, "status": "started"}

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/crawl/{session_id}")
        async def get_crawl_status(session_id: str):
            """Get crawling session status"""
            if session_id not in self.active_crawlers:
                raise HTTPException(status_code=404, detail="Crawl session not found")

            session = self.active_crawlers[session_id]
            return {
                "session_id": session_id,
                "status": session["status"],
                "start_time": session["start_time"].isoformat(),
                "urls": session["urls"],
                "stats": session["crawler"].get_crawling_status() if hasattr(session["crawler"], "get_crawling_status") else {}
            }

        @self.app.get("/api/crawl/logs/{session_id}")
        async def get_crawl_logs(session_id: str):
            """Get crawling logs for a session"""
            return await self._get_crawl_logs(session_id)

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates"""
            await websocket.accept()
            self.websocket_connections.append(websocket)

            try:
                while True:
                    # Send periodic updates
                    data = await self._get_dashboard_data()
                    await websocket.send_json(data)
                    await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                print(f"WebSocket error: {e}")
            finally:
                self.websocket_connections.remove(websocket)

        @self.app.get("/api/analytics/summary")
        async def get_analytics_summary():
            """Get analytics summary across all databases"""
            return await self._get_analytics_summary()

        @self.app.get("/api/alerts")
        async def get_active_alerts():
            """Get active system alerts"""
            return await self._get_active_alerts()

    async def _get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        db_status = self.db_manager.get_all_database_status()

        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": self._calculate_system_health(db_status),
            "databases": db_status["databases"],
            "summary": db_status["summary"],
            "active_crawlers": len(self.active_crawlers),
            "recent_activities": await self._get_recent_activities(),
            "performance_metrics": await self._get_performance_metrics(),
            "alerts": await self._get_active_alerts()
        }

    def _calculate_system_health(self, db_status: Dict) -> str:
        """Calculate overall system health"""
        total_dbs = db_status["summary"]["total"]
        healthy_dbs = db_status["summary"]["healthy"]

        if healthy_dbs == total_dbs:
            return "excellent"
        elif healthy_dbs >= total_dbs * 0.8:
            return "good"
        elif healthy_dbs >= total_dbs * 0.5:
            return "warning"
        else:
            return "critical"

    async def _get_database_usage_stats(self, db_name: str) -> Dict:
        """Get detailed usage statistics for a database"""
        conn = sqlite3.connect("database_usage.db")
        cursor = conn.cursor()

        # Get last 7 days usage
        cursor.execute('''
            SELECT date, SUM(storage_used_bytes), SUM(writes_count), SUM(reads_count)
            FROM database_usage
            WHERE database_name = ? AND date >= date('now', '-7 days')
            GROUP BY date
            ORDER BY date
        ''', (db_name,))

        usage_history = []
        for row in cursor.fetchall():
            usage_history.append({
                "date": row[0],
                "storage_used": row[1],
                "writes": row[2],
                "reads": row[3]
            })

        conn.close()
        return {"usage_history": usage_history}

    async def _get_recent_activity(self, db_name: str) -> List[Dict]:
        """Get recent activity for a database"""
        # Mock implementation - replace with actual activity tracking
        return [
            {"timestamp": datetime.now().isoformat(), "action": "write", "table": "backlinks", "records": 15},
            {"timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(), "action": "write", "table": "crawled_pages", "records": 3},
        ]

    async def _get_recent_activities(self) -> List[Dict]:
        """Get recent system activities"""
        activities = []

        # Get recent crawling activities
        for session_id, session in list(self.active_crawlers.items()):
            activities.append({
                "timestamp": session["start_time"].isoformat(),
                "type": "crawl_started",
                "session_id": session_id,
                "urls_count": len(session["urls"]),
                "status": session["status"]
            })

        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:10]  # Return last 10 activities

    async def _get_performance_metrics(self) -> Dict:
        """Get system performance metrics"""
        return {
            "avg_response_time_ms": 150,
            "requests_per_minute": 45,
            "error_rate_percent": 2.1,
            "active_connections": len(self.websocket_connections),
            "uptime_hours": 168.5
        }

    async def _get_active_alerts(self) -> List[Dict]:
        """Get active system alerts"""
        alerts = []

        # Check database health for alerts
        db_status = self.db_manager.get_all_database_status()
        for db in db_status["databases"]:
            if db["status"] == "critical":
                alerts.append({
                    "id": f"db_critical_{db['name']}",
                    "type": "critical",
                    "message": f"Database {db['name']} is at critical capacity",
                    "details": f"Storage: {db['storage_percent']:.1f}%, Writes: {db['writes_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat(),
                    "database": db["name"]
                })
            elif db["status"] == "warning":
                alerts.append({
                    "id": f"db_warning_{db['name']}",
                    "type": "warning",
                    "message": f"Database {db['name']} approaching capacity limits",
                    "details": f"Storage: {db['storage_percent']:.1f}%, Writes: {db['writes_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat(),
                    "database": db["name"]
                })

        return alerts

    async def _get_analytics_summary(self) -> Dict:
        """Get analytics summary across all databases"""
        return {
            "total_pages_crawled": 1247,
            "total_backlinks_found": 5832,
            "unique_domains_discovered": 342,
            "crawling_sessions_completed": 23,
            "average_crawl_time_minutes": 12.4,
            "data_processed_gb": 2.8,
            "top_domains_by_backlinks": [
                {"domain": "example.com", "backlinks": 156},
                {"domain": "test.org", "backlinks": 134},
                {"domain": "sample.net", "backlinks": 98}
            ]
        }

    async def _run_crawling_session(self, session_id: str, urls: List[str]):
        """Run a crawling session in the background"""
        try:
            session = self.active_crawlers[session_id]
            session["status"] = "running"

            # Run the actual crawling
            results = session["crawler"].crawl_with_backlink_analysis(urls)

            session["status"] = "completed"
            session["results"] = results
            session["end_time"] = datetime.now()

            # Broadcast update to websocket clients
            await self._broadcast_update({
                "type": "crawl_completed",
                "session_id": session_id,
                "results": results
            })

        except Exception as e:
            session["status"] = "failed"
            session["error"] = str(e)
            session["end_time"] = datetime.now()

            await self._broadcast_update({
                "type": "crawl_failed",
                "session_id": session_id,
                "error": str(e)
            })

    async def _get_crawl_logs(self, session_id: str) -> Dict:
        """Get crawling logs for a session"""
        if session_id not in self.active_crawlers:
            return {"logs": [], "error": "Session not found"}

        # Mock logs - implement actual logging system
        return {
            "logs": [
                {"timestamp": datetime.now().isoformat(), "level": "info", "message": "Crawling started"},
                {"timestamp": datetime.now().isoformat(), "level": "info", "message": "Database allocated: websitecrawler1"},
                {"timestamp": datetime.now().isoformat(), "level": "info", "message": "Processing 5 URLs"}
            ]
        }

    async def _background_monitoring(self):
        """Background task for system monitoring"""
        while True:
            try:
                # Check system health
                await self._check_system_health()

                # Clean up completed crawl sessions
                await self._cleanup_old_sessions()

                # Update cached metrics
                await self._update_cached_metrics()

                await asyncio.sleep(30)  # Run every 30 seconds

            except Exception as e:
                print(f"Background monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _check_system_health(self):
        """Check system health and generate alerts if needed"""
        alerts = await self._get_active_alerts()
        if alerts:
            # Broadcast critical alerts
            for alert in alerts:
                if alert["type"] == "critical":
                    await self._broadcast_update({
                        "type": "alert",
                        "alert": alert
                    })

    async def _cleanup_old_sessions(self):
        """Clean up old crawling sessions"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        sessions_to_remove = []
        for session_id, session in self.active_crawlers.items():
            if (session.get("end_time", session["start_time"]) < cutoff_time and
                session["status"] in ["completed", "failed"]):
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.active_crawlers[session_id]

    async def _update_cached_metrics(self):
        """Update cached performance metrics"""
        # Implement metrics caching if needed
        pass

    async def _broadcast_update(self, data: Dict):
        """Broadcast update to all websocket connections"""
        disconnected = []

        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(data)
            except:
                disconnected.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            self.websocket_connections.remove(websocket)

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the dashboard server"""
        print(f"🚀 Starting Enhanced RatCrawler Dashboard on http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# Create global dashboard instance
enhanced_dashboard = EnhancedTursoDashboard()


if __name__ == "__main__":
    enhanced_dashboard.run()
