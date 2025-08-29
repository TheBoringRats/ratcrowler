"""
Turso Database Monitoring Dashboard with FastAPI
Monitors multiple Turso databases, handles rotation, and provides web dashboard
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

import requests
import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import schedule


class DatabaseConfig(BaseModel):
    name: str
    url: str
    auth_token: str
    monthly_write_limit: int = 10_000_000  # 10M writes per month
    storage_quota_gb: float = 5.0  # 5GB storage


class TursoMonitor:
    def __init__(self, local_db_path: str = "turso_monitor.db"):
        self.local_db_path = local_db_path
        self.databases: Dict[str, DatabaseConfig] = {}
        self.usage_cache: Dict[str, Dict] = {}
        self.init_local_db()

    def init_local_db(self):
        """Initialize local SQLite database for tracking"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()

        # Database configurations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS databases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                auth_token TEXT NOT NULL,
                monthly_write_limit INTEGER DEFAULT 10000000,
                storage_quota_gb REAL DEFAULT 5.0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                database_name TEXT NOT NULL,
                date DATE NOT NULL,
                storage_bytes INTEGER DEFAULT 0,
                rows_written INTEGER DEFAULT 0,
                rows_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(database_name, date)
            )
        ''')

        # Monthly write tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_writes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                database_name TEXT NOT NULL,
                year_month TEXT NOT NULL,
                total_writes INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(database_name, year_month)
            )
        ''')

        conn.commit()
        conn.close()

    def add_database(self, config: DatabaseConfig):
        """Add a new database to monitor"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO databases
            (name, url, auth_token, monthly_write_limit, storage_quota_gb)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            config.name,
            config.url,
            config.auth_token,
            config.monthly_write_limit,
            config.storage_quota_gb
        ))

        conn.commit()
        conn.close()
        self.databases[config.name] = config

    def remove_database(self, name: str):
        """Remove a database from monitoring"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()

        cursor.execute('UPDATE databases SET is_active = 0 WHERE name = ?', (name,))

        conn.commit()
        conn.close()

        if name in self.databases:
            del self.databases[name]

    def get_all_databases(self) -> List[Dict]:
        """Get all active databases"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT name, url, auth_token, monthly_write_limit, storage_quota_gb
            FROM databases
            WHERE is_active = 1
        ''')

        databases = []
        for row in cursor.fetchall():
            databases.append({
                'name': row[0],
                'url': row[1],
                'auth_token': row[2],
                'monthly_write_limit': row[3],
                'storage_quota_gb': row[4]
            })

        conn.close()
        return databases

    def get_database_usage(self, db_name: str) -> Dict:
        """Get current usage for a specific database"""
        if db_name not in self.databases:
            return {}

        config = self.databases[db_name]

        try:
            # Get today's usage from Turso API
            today = datetime.utcnow().date()
            url = f"{config.url}/usage"

            headers = {
                "Authorization": f"Bearer {config.auth_token}",
                "Content-Type": "application/json"
            }

            params = {
                "from": f"{today}T00:00:00Z",
                "to": f"{today}T23:59:59Z"
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            total = data.get("database", {}).get("total", {})
            storage_used = total.get("storage_bytes", 0)
            writes_used = total.get("rows_written", 0)
            reads_used = total.get("rows_read", 0)

            # Store in local database
            self._store_usage(db_name, today, storage_used, writes_used, reads_used)

            return {
                'database_name': db_name,
                'storage_used': storage_used,
                'writes_used': writes_used,
                'reads_used': reads_used,
                'storage_quota': int(config.storage_quota_gb * 1024**3),
                'monthly_write_limit': config.monthly_write_limit,
                'last_updated': datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"Error fetching usage for {db_name}: {e}")
            return self._get_cached_usage(db_name)

    def _store_usage(self, db_name: str, date, storage_bytes: int, writes: int, reads: int):
        """Store usage data in local database"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO usage_history
            (database_name, date, storage_bytes, rows_written, rows_read)
            VALUES (?, ?, ?, ?, ?)
        ''', (db_name, date.isoformat(), storage_bytes, writes, reads))

        conn.commit()
        conn.close()

    def _get_cached_usage(self, db_name: str) -> Dict:
        """Get cached usage data"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT storage_bytes, rows_written, rows_read
            FROM usage_history
            WHERE database_name = ?
            ORDER BY date DESC
            LIMIT 1
        ''', (db_name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'database_name': db_name,
                'storage_used': row[0],
                'writes_used': row[1],
                'reads_used': row[2],
                'cached': True
            }

        return {'database_name': db_name, 'error': 'No data available'}

    def get_monthly_writes(self, db_name: str, year_month: Optional[str] = None) -> int:
        """Get monthly write count for a database"""
        if not year_month:
            now = datetime.utcnow()
            year_month = f"{now.year}-{now.month:02d}"

        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT total_writes FROM monthly_writes
            WHERE database_name = ? AND year_month = ?
        ''', (db_name, year_month))

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else 0

    def update_monthly_writes(self, db_name: str, additional_writes: int):
        """Update monthly write count"""
        now = datetime.utcnow()
        year_month = f"{now.year}-{now.month:02d}"

        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()

        # Get current count
        current_writes = self.get_monthly_writes(db_name, year_month)

        # Update or insert
        cursor.execute('''
            INSERT OR REPLACE INTO monthly_writes
            (database_name, year_month, total_writes, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (db_name, year_month, current_writes + additional_writes, now))

        conn.commit()
        conn.close()

    def get_available_database(self) -> Optional[str]:
        """Get the best available database for writing"""
        databases = self.get_all_databases()

        for db in databases:
            db_name = db['name']
            monthly_writes = self.get_monthly_writes(db_name)
            usage = self.get_database_usage(db_name)

            # Check if database has capacity
            write_limit = db['monthly_write_limit']
            storage_quota = int(db['storage_quota_gb'] * 1024**3)
            storage_used = usage.get('storage_used', 0)

            # Must have less than 90% of monthly writes and 90% storage used
            if (monthly_writes < write_limit * 0.9 and
                storage_used < storage_quota * 0.9):
                return db_name

        return None

    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        databases = self.get_all_databases()
        dashboard_data = {
            'databases': [],
            'summary': {
                'total_databases': len(databases),
                'active_databases': 0,
                'warning_databases': 0,
                'critical_databases': 0,
                'total_storage_used': 0,
                'total_storage_quota': 0
            },
            'last_updated': datetime.utcnow().isoformat()
        }

        for db in databases:
            db_name = db['name']
            usage = self.get_database_usage(db_name)
            monthly_writes = self.get_monthly_writes(db_name)

            # Calculate percentages
            storage_quota = int(db['storage_quota_gb'] * 1024**3)
            storage_used = usage.get('storage_used', 0)
            storage_percent = (storage_used / storage_quota * 100) if storage_quota > 0 else 0

            write_limit = db['monthly_write_limit']
            write_percent = (monthly_writes / write_limit * 100) if write_limit > 0 else 0

            # Determine status
            if storage_percent >= 90 or write_percent >= 90:
                status = 'critical'
                dashboard_data['summary']['critical_databases'] += 1
            elif storage_percent >= 70 or write_percent >= 70:
                status = 'warning'
                dashboard_data['summary']['warning_databases'] += 1
            else:
                status = 'healthy'
                dashboard_data['summary']['active_databases'] += 1

            db_data = {
                'name': db_name,
                'status': status,
                'storage_used': storage_used,
                'storage_quota': storage_quota,
                'storage_percent': round(storage_percent, 2),
                'monthly_writes': monthly_writes,
                'write_limit': write_limit,
                'write_percent': round(write_percent, 2),
                'last_updated': usage.get('last_updated', 'Unknown')
            }

            dashboard_data['databases'].append(db_data)
            dashboard_data['summary']['total_storage_used'] += storage_used
            dashboard_data['summary']['total_storage_quota'] += storage_quota

        return dashboard_data


# Global monitor instance
monitor = TursoMonitor()


# FastAPI Application
app = FastAPI(title="Turso Database Monitor", version="1.0.0")

# Create templates directory if it doesn't exist
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    data = monitor.get_dashboard_data()
    return templates.TemplateResponse("dashboard.html", {"request": request, "data": data})


@app.get("/api/databases", response_model=List[Dict])
async def get_databases():
    """Get all databases"""
    return monitor.get_all_databases()


@app.get("/api/database/{db_name}")
async def get_database(db_name: str):
    """Get specific database details"""
    usage = monitor.get_database_usage(db_name)
    if not usage:
        raise HTTPException(status_code=404, detail="Database not found")

    monthly_writes = monitor.get_monthly_writes(db_name)
    return {
        **usage,
        'monthly_writes': monthly_writes
    }


@app.post("/api/database")
async def add_database(config: DatabaseConfig):
    """Add a new database"""
    monitor.add_database(config)
    return {"message": f"Database {config.name} added successfully"}


@app.delete("/api/database/{db_name}")
async def remove_database(db_name: str):
    """Remove a database"""
    monitor.remove_database(db_name)
    return {"message": f"Database {db_name} removed successfully"}


@app.get("/api/dashboard")
async def get_dashboard_data():
    """Get dashboard data as JSON"""
    return monitor.get_dashboard_data()


@app.get("/api/available-database")
async def get_available_database():
    """Get the best available database for writing"""
    db_name = monitor.get_available_database()
    if db_name:
        return {"database": db_name}
    else:
        raise HTTPException(status_code=503, detail="No available databases")


@app.post("/api/record-writes/{db_name}")
async def record_writes(db_name: str, writes: int):
    """Record write operations for a database"""
    monitor.update_monthly_writes(db_name, writes)
    return {"message": f"Recorded {writes} writes for {db_name}"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


async def background_monitoring():
    """Background task to monitor databases periodically"""
    while True:
        try:
            # Update usage for all databases
            databases = monitor.get_all_databases()
            for db in databases:
                monitor.get_database_usage(db['name'])

            # Clean up old usage data (keep last 30 days)
            cleanup_old_data()

        except Exception as e:
            print(f"Background monitoring error: {e}")

        await asyncio.sleep(300)  # Update every 5 minutes


def cleanup_old_data():
    """Clean up old usage data"""
    conn = sqlite3.connect(monitor.local_db_path)
    cursor = conn.cursor()

    # Keep only last 30 days of usage history
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).date()

    cursor.execute('''
        DELETE FROM usage_history
        WHERE date < ?
    ''', (thirty_days_ago.isoformat(),))

    conn.commit()
    conn.close()


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    # Load existing databases
    databases = monitor.get_all_databases()
    for db in databases:
        config = DatabaseConfig(**db)
        monitor.databases[db['name']] = config

    # Start background monitoring
    asyncio.create_task(background_monitoring())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

import json
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from rat.turso_connection import get_turso_manager, DatabaseUsage
import threading
import time


class TursoMonitoringDashboard:
    """Web dashboard for monitoring Turso databases"""

    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        self.app = Flask(__name__,
                        template_folder='templates',
                        static_folder='static')
        self.host = host
        self.port = port
        self.manager = get_turso_manager()

        # Setup routes
        self._setup_routes()

        # Start background monitoring
        self._start_background_monitoring()

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')

        @self.app.route('/api/databases')
        def get_databases():
            """API endpoint to get all databases"""
            try:
                databases = []
                for db_name, db_info in self.manager.databases.items():
                    usage = self.manager.get_database_usage(db_name)
                    if usage:
                        databases.append({
                            'name': db_info.name,
                            'url': db_info.url,
                            'org_slug': db_info.org_slug,
                            'is_active': db_info.is_active,
                            'usage': {
                                'storage_used': usage.storage_used,
                                'storage_quota': usage.storage_quota,
                                'storage_pct': (usage.storage_used / usage.storage_quota) * 100,
                                'daily_writes': usage.daily_writes,
                                'daily_quota': usage.daily_quota,
                                'daily_pct': (usage.daily_writes / usage.daily_quota) * 100,
                                'monthly_writes': usage.monthly_writes,
                                'monthly_quota': usage.monthly_quota,
                                'monthly_pct': (usage.monthly_writes / usage.monthly_quota) * 100,
                                'last_updated': usage.last_updated.isoformat()
                            }
                        })

                return jsonify({
                    'success': True,
                    'databases': databases,
                    'total_databases': len(databases)
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/alerts')
        def get_alerts():
            """API endpoint to get current alerts"""
            try:
                # Get alerts from database
                cursor = self.manager.monitoring_db.cursor()
                cursor.execute('''
                    SELECT db_name, alert_type, message, severity, timestamp
                    FROM alerts
                    WHERE resolved = FALSE
                    ORDER BY timestamp DESC
                    LIMIT 50
                ''')

                alerts = []
                for row in cursor.fetchall():
                    alerts.append({
                        'db_name': row[0],
                        'alert_type': row[1],
                        'message': row[2],
                        'severity': row[3],
                        'timestamp': row[4]
                    })

                return jsonify({
                    'success': True,
                    'alerts': alerts,
                    'total_alerts': len(alerts)
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/add_database', methods=['POST'])
        def add_database():
            """API endpoint to add a new database"""
            try:
                data = request.get_json()

                required_fields = ['name', 'url', 'auth_token', 'org_slug']
                for field in required_fields:
                    if field not in data:
                        return jsonify({
                            'success': False,
                            'error': f'Missing required field: {field}'
                        }), 400

                self.manager.add_database(
                    name=data['name'],
                    url=data['url'],
                    auth_token=data['auth_token'],
                    org_slug=data['org_slug']
                )

                return jsonify({
                    'success': True,
                    'message': f'Database {data["name"]} added successfully'
                })

            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/toggle_database/<db_name>', methods=['POST'])
        def toggle_database(db_name):
            """API endpoint to activate/deactivate a database"""
            try:
                data = request.get_json()
                action = data.get('action', 'toggle')

                if action == 'activate':
                    self.manager.activate_database(db_name)
                    message = f'Database {db_name} activated'
                elif action == 'deactivate':
                    self.manager.deactivate_database(db_name)
                    message = f'Database {db_name} deactivated'
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid action. Use "activate" or "deactivate"'
                    }), 400

                return jsonify({
                    'success': True,
                    'message': message
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/usage_history/<db_name>')
        def get_usage_history(db_name):
            """API endpoint to get usage history for a database"""
            try:
                cursor = self.manager.monitoring_db.cursor()
                cursor.execute('''
                    SELECT storage_used, daily_writes, monthly_writes, last_updated
                    FROM database_usage
                    WHERE db_name = ?
                    ORDER BY last_updated DESC
                    LIMIT 30
                ''', (db_name,))

                history = []
                for row in cursor.fetchall():
                    history.append({
                        'storage_used': row[0],
                        'daily_writes': row[1],
                        'monthly_writes': row[2],
                        'timestamp': row[3]
                    })

                return jsonify({
                    'success': True,
                    'database': db_name,
                    'history': history
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/system_stats')
        def get_system_stats():
            """API endpoint to get overall system statistics"""
            try:
                stats = self.manager.get_all_usage_stats()

                total_storage = sum(s.storage_used for s in stats)
                total_daily_writes = sum(s.daily_writes for s in stats)
                total_monthly_writes = sum(s.monthly_writes for s in stats)

                # Calculate averages
                avg_storage_pct = sum((s.storage_used / s.storage_quota) * 100 for s in stats) / len(stats) if stats else 0
                avg_daily_pct = sum((s.daily_writes / s.daily_quota) * 100 for s in stats) / len(stats) if stats else 0
                avg_monthly_pct = sum((s.monthly_writes / s.monthly_quota) * 100 for s in stats) / len(stats) if stats else 0

                return jsonify({
                    'success': True,
                    'system_stats': {
                        'total_databases': len(stats),
                        'total_storage_used': total_storage,
                        'total_daily_writes': total_daily_writes,
                        'total_monthly_writes': total_monthly_writes,
                        'avg_storage_pct': avg_storage_pct,
                        'avg_daily_pct': avg_daily_pct,
                        'avg_monthly_pct': avg_monthly_pct
                    }
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

    def _start_background_monitoring(self):
        """Start background monitoring tasks"""

        def monitoring_task():
            """Periodic monitoring task"""
            while True:
                try:
                    # Check and create alerts
                    alerts = self.manager.check_and_create_alerts()

                    # Clean old data (keep last 30 days)
                    cursor = self.manager.monitoring_db.cursor()
                    cursor.execute("DELETE FROM write_log WHERE timestamp < datetime('now', '-30 days')")
                    cursor.execute("DELETE FROM alerts WHERE timestamp < datetime('now', '-30 days') AND resolved = TRUE")
                    self.manager.monitoring_db.commit()

                    print(f"📊 Monitoring cycle completed. Found {len(alerts)} alerts.")

                except Exception as e:
                    print(f"❌ Monitoring error: {e}")

                # Run every 5 minutes
                time.sleep(300)

        def monthly_reset_task():
            """Monthly reset task for write counters"""
            while True:
                now = datetime.now()

                # Reset on the 1st of each month
                if now.day == 1 and now.hour == 0:
                    try:
                        self.manager.reset_monthly_counters()
                        print("🔄 Monthly counters reset")
                    except Exception as e:
                        print(f"❌ Monthly reset error: {e}")

                # Check every hour
                time.sleep(3600)

        # Start background threads
        threading.Thread(target=monitoring_task, daemon=True).start()
        threading.Thread(target=monthly_reset_task, daemon=True).start()

    def run(self):
        """Run the dashboard server"""
        print(f"🚀 Starting Turso Monitoring Dashboard on http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False)


# HTML Template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Turso Database Monitor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-800 mb-2">🗄️ Turso Database Monitor</h1>
            <p class="text-gray-600">Monitor multiple Turso databases with real-time analytics</p>
        </header>

        <!-- System Overview -->
        <div id="system-overview" class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <!-- Cards will be populated by JavaScript -->
        </div>

        <!-- Database List -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold">Databases</h2>
                <button onclick="showAddDatabaseModal()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
                    + Add Database
                </button>
            </div>
            <div id="databases-list" class="space-y-4">
                <!-- Database cards will be populated by JavaScript -->
            </div>
        </div>

        <!-- Alerts -->
        <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold mb-4">🚨 Active Alerts</h2>
            <div id="alerts-list">
                <!-- Alerts will be populated by JavaScript -->
            </div>
        </div>
    </div>

    <!-- Add Database Modal -->
    <div id="addDatabaseModal" class="fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center">
        <div class="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 class="text-lg font-semibold mb-4">Add New Database</h3>
            <form id="addDatabaseForm">
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-1">Database Name</label>
                    <input type="text" name="name" required class="w-full border rounded px-3 py-2">
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-1">Database URL</label>
                    <input type="url" name="url" required class="w-full border rounded px-3 py-2">
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-1">Auth Token</label>
                    <input type="password" name="auth_token" required class="w-full border rounded px-3 py-2">
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-1">Organization Slug</label>
                    <input type="text" name="org_slug" required class="w-full border rounded px-3 py-2">
                </div>
                <div class="flex justify-end space-x-2">
                    <button type="button" onclick="hideAddDatabaseModal()" class="px-4 py-2 text-gray-600">Cancel</button>
                    <button type="submit" class="px-4 py-2 bg-blue-500 text-white rounded">Add Database</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let refreshInterval;

        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadSystemOverview();
            loadDatabases();
            loadAlerts();

            // Auto-refresh every 30 seconds
            refreshInterval = setInterval(() => {
                loadSystemOverview();
                loadDatabases();
                loadAlerts();
            }, 30000);
        });

        async function loadSystemOverview() {
            try {
                const response = await fetch('/api/system_stats');
                const data = await response.json();

                if (data.success) {
                    const stats = data.system_stats;
                    const overview = document.getElementById('system-overview');

                    overview.innerHTML = `
                        <div class="bg-white p-4 rounded-lg shadow">
                            <h3 class="text-lg font-semibold text-gray-800">Total Databases</h3>
                            <p class="text-2xl font-bold text-blue-600">${stats.total_databases}</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow">
                            <h3 class="text-lg font-semibold text-gray-800">Storage Used</h3>
                            <p class="text-2xl font-bold text-green-600">${formatBytes(stats.total_storage_used)}</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow">
                            <h3 class="text-lg font-semibold text-gray-800">Daily Writes</h3>
                            <p class="text-2xl font-bold text-purple-600">${stats.total_daily_writes.toLocaleString()}</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow">
                            <h3 class="text-lg font-semibold text-gray-800">Avg Usage</h3>
                            <p class="text-2xl font-bold text-orange-600">${stats.avg_storage_pct.toFixed(1)}%</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading system overview:', error);
            }
        }

        async function loadDatabases() {
            try {
                const response = await fetch('/api/databases');
                const data = await response.json();

                if (data.success) {
                    const container = document.getElementById('databases-list');
                    container.innerHTML = '';

                    data.databases.forEach(db => {
                        const usage = db.usage;
                        const storagePct = usage.storage_pct;
                        const dailyPct = usage.daily_pct;
                        const monthlyPct = usage.monthly_pct;

                        // Determine status color
                        let statusColor = 'green';
                        if (storagePct > 90 || dailyPct > 90 || monthlyPct > 90) {
                            statusColor = 'red';
                        } else if (storagePct > 70 || dailyPct > 70 || monthlyPct > 70) {
                            statusColor = 'yellow';
                        }

                        const card = document.createElement('div');
                        card.className = `border rounded-lg p-4 ${db.is_active ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`;

                        card.innerHTML = `
                            <div class="flex justify-between items-start mb-2">
                                <h3 class="text-lg font-semibold">${db.name}</h3>
                                <div class="flex items-center space-x-2">
                                    <span class="px-2 py-1 text-xs rounded ${db.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                                        ${db.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                    <button onclick="toggleDatabase('${db.name}')" class="text-sm text-blue-600 hover:text-blue-800">
                                        ${db.is_active ? 'Deactivate' : 'Activate'}
                                    </button>
                                </div>
                            </div>

                            <div class="grid grid-cols-3 gap-4 text-sm">
                                <div>
                                    <p class="text-gray-600">Storage</p>
                                    <p class="font-semibold">${formatBytes(usage.storage_used)} / ${formatBytes(usage.storage_quota)}</p>
                                    <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                                        <div class="bg-${statusColor}-500 h-2 rounded-full" style="width: ${storagePct}%"></div>
                                    </div>
                                </div>
                                <div>
                                    <p class="text-gray-600">Daily Writes</p>
                                    <p class="font-semibold">${usage.daily_writes.toLocaleString()} / ${usage.daily_quota.toLocaleString()}</p>
                                    <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                                        <div class="bg-${statusColor}-500 h-2 rounded-full" style="width: ${dailyPct}%"></div>
                                    </div>
                                </div>
                                <div>
                                    <p class="text-gray-600">Monthly Writes</p>
                                    <p class="font-semibold">${usage.monthly_writes.toLocaleString()} / ${usage.monthly_quota.toLocaleString()}</p>
                                    <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                                        <div class="bg-${statusColor}-500 h-2 rounded-full" style="width: ${monthlyPct}%"></div>
                                    </div>
                                </div>
                            </div>
                        `;

                        container.appendChild(card);
                    });
                }
            } catch (error) {
                console.error('Error loading databases:', error);
            }
        }

        async function loadAlerts() {
            try {
                const response = await fetch('/api/alerts');
                const data = await response.json();

                if (data.success) {
                    const container = document.getElementById('alerts-list');

                    if (data.alerts.length === 0) {
                        container.innerHTML = '<p class="text-gray-500 text-center py-4">No active alerts</p>';
                        return;
                    }

                    container.innerHTML = '';
                    data.alerts.forEach(alert => {
                        const alertDiv = document.createElement('div');
                        alertDiv.className = `p-3 rounded mb-2 ${
                            alert.severity === 'CRITICAL' ? 'bg-red-100 border-red-300' :
                            alert.severity === 'WARNING' ? 'bg-yellow-100 border-yellow-300' :
                            'bg-blue-100 border-blue-300'
                        } border-l-4`;

                        alertDiv.innerHTML = `
                            <div class="flex justify-between items-start">
                                <div>
                                    <span class="font-semibold">${alert.db_name}</span>
                                    <span class="text-sm text-gray-600">(${alert.alert_type})</span>
                                    <p class="text-sm mt-1">${alert.message}</p>
                                </div>
                                <span class="text-xs text-gray-500">${new Date(alert.timestamp).toLocaleString()}</span>
                            </div>
                        `;

                        container.appendChild(alertDiv);
                    });
                }
            } catch (error) {
                console.error('Error loading alerts:', error);
            }
        }

        function showAddDatabaseModal() {
            document.getElementById('addDatabaseModal').classList.remove('hidden');
        }

        function hideAddDatabaseModal() {
            document.getElementById('addDatabaseModal').classList.add('hidden');
        }

        document.getElementById('addDatabaseForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);

            try {
                const response = await fetch('/api/add_database', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    alert('Database added successfully!');
                    hideAddDatabaseModal();
                    e.target.reset();
                    loadDatabases();
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error adding database: ' + error.message);
            }
        });

        async function toggleDatabase(dbName) {
            try {
                const response = await fetch(`/api/toggle_database/${dbName}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ action: 'toggle' })
                });

                const result = await response.json();

                if (result.success) {
                    loadDatabases();
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error toggling database: ' + error.message);
            }
        }

        function formatBytes(bytes) {
            const units = ['B', 'KB', 'MB', 'GB', 'TB'];
            let size = bytes;
            let unitIndex = 0;

            while (size >= 1024 && unitIndex < units.length - 1) {
                size /= 1024;
                unitIndex++;
            }

            return `${size.toFixed(1)} ${units[unitIndex]}`;
        }
    </script>
</body>
</html>
"""


def create_dashboard_app():
    """Create and return the dashboard Flask app"""
    dashboard = TursoMonitoringDashboard()
    return dashboard.app


def run_dashboard(host: str = '0.0.0.0', port: int = 5000):
    """Run the monitoring dashboard"""
    dashboard = TursoMonitoringDashboard(host, port)
    dashboard.run()


if __name__ == "__main__":
    print("🚀 Starting Turso Database Monitoring Dashboard...")
    run_dashboard()
