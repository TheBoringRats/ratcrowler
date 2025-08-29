"""
Turso Multi-Database Connection Manager
Provides seamless integration with multiple Turso databases with monitoring and auto-switching.
"""

import sqlite3
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List, Union
from dataclasses import dataclass
from rat.config import config

try:
    from libsql_client import create_client
    TURSO_AVAILABLE = True
except ImportError:
    TURSO_AVAILABLE = False
    create_client = None


@dataclass
class DatabaseInfo:
    """Database connection information"""
    name: str
    url: str
    auth_token: str
    org_slug: str
    is_active: bool = True
    monthly_writes: int = 0
    last_reset: Optional[datetime] = None


@dataclass
class DatabaseUsage:
    """Database usage statistics"""
    name: str
    storage_used: int
    storage_quota: int
    daily_writes: int
    daily_quota: int
    monthly_writes: int
    monthly_quota: int
    last_updated: datetime


class TursoMultiDatabaseManager:
    """Manages multiple Turso databases with monitoring and auto-switching"""

    def __init__(self, config_file: str = "turso_databases.json"):
        self.config_file = config_file
        self.databases: Dict[str, DatabaseInfo] = {}
        self.usage_cache: Dict[str, DatabaseUsage] = {}
        self.current_db_index = 0

        # Quotas
        self.STORAGE_QUOTA_BYTES = 5 * 1024**3  # 5GB
        self.DAILY_WRITE_QUOTA = 10_000_000     # 10M writes/day
        self.MONTHLY_WRITE_QUOTA = 10_000_000   # 10M writes/month

        self.load_databases()
        self._init_monitoring_db()

    def _init_monitoring_db(self):
        """Initialize local monitoring database"""
        self.monitoring_db = sqlite3.connect("turso_monitoring.db")
        cursor = self.monitoring_db.cursor()

        # Database usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS database_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                db_name TEXT NOT NULL,
                storage_used INTEGER,
                daily_writes INTEGER,
                monthly_writes INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(db_name, last_updated)
            )
        ''')

        # Write operations log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS write_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                db_name TEXT NOT NULL,
                operation_type TEXT,
                record_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Alerts and warnings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                db_name TEXT NOT NULL,
                alert_type TEXT,
                message TEXT,
                severity TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')

        self.monitoring_db.commit()

    def load_databases(self):
        """Load database configurations from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                for db_data in data.get('databases', []):
                    db_info = DatabaseInfo(**db_data)
                    self.databases[db_info.name] = db_info
        else:
            # Create default configuration
            self._create_default_config()

    def _create_default_config(self):
        """Create default database configuration"""
        default_config = {
            "databases": [
                {
                    "name": "primary_db",
                    "url": config.TURSO_DATABASE_URL or "",
                    "auth_token": config.TURSO_AUTH_TOKEN or "",
                    "org_slug": getattr(config, 'TURSO_ORG_SLUG', ""),
                    "is_active": True,
                    "monthly_writes": 0,
                    "last_reset": datetime.now().isoformat()
                }
            ]
        }

        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        print(f"✅ Created default Turso database config: {self.config_file}")

    def add_database(self, name: str, url: str, auth_token: str, org_slug: str):
        """Add a new database to the pool"""
        if name in self.databases:
            raise ValueError(f"Database '{name}' already exists")

        db_info = DatabaseInfo(
            name=name,
            url=url,
            auth_token=auth_token,
            org_slug=org_slug,
            monthly_writes=0,
            last_reset=datetime.now()
        )

        self.databases[name] = db_info
        self.save_databases()

        print(f"✅ Added database: {name}")

    def save_databases(self):
        """Save database configurations to file"""
        data = {
            "databases": [
                {
                    "name": db.name,
                    "url": db.url,
                    "auth_token": db.auth_token,
                    "org_slug": db.org_slug,
                    "is_active": db.is_active,
                    "monthly_writes": db.monthly_writes,
                    "last_reset": db.last_reset.isoformat() if db.last_reset else None
                }
                for db in self.databases.values()
            ]
        }

        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_next_available_database(self) -> Optional[DatabaseInfo]:
        """Get the next available database based on quotas"""
        active_dbs = [db for db in self.databases.values() if db.is_active]

        if not active_dbs:
            return None

        # Check each database for availability
        for db in active_dbs:
            usage = self.get_database_usage(db.name)
            if usage:
                # Check if database has capacity
                storage_pct = (usage.storage_used / usage.storage_quota) * 100
                daily_pct = (usage.daily_writes / usage.daily_quota) * 100
                monthly_pct = (usage.monthly_writes / usage.monthly_quota) * 100

                # Database is available if under 90% capacity
                if storage_pct < 90 and daily_pct < 90 and monthly_pct < 90:
                    return db

        return None

    def get_database_usage(self, db_name: str) -> Optional[DatabaseUsage]:
        """Get current usage for a database"""
        if db_name in self.usage_cache:
            # Return cached data if less than 5 minutes old
            cached = self.usage_cache[db_name]
            if (datetime.now() - cached.last_updated).seconds < 300:
                return cached

        db_info = self.databases.get(db_name)
        if not db_info:
            return None

        try:
            # Fetch usage from Turso API
            usage = self._fetch_turso_usage(db_info)
            self.usage_cache[db_name] = usage

            # Store in monitoring database
            self._store_usage_in_monitoring_db(usage)

            return usage

        except Exception as e:
            print(f"❌ Failed to fetch usage for {db_name}: {e}")
            return None

    def _fetch_turso_usage(self, db_info: DatabaseInfo) -> DatabaseUsage:
        """Fetch database usage from Turso API"""
        url = f"https://api.turso.tech/v1/organizations/{db_info.org_slug}/databases/{db_info.name}/usage"

        today = datetime.utcnow().date()
        params = {
            "from": f"{today}T00:00:00Z",
            "to": f"{today}T23:59:59Z"
        }

        headers = {
            "Authorization": f"Bearer {db_info.auth_token}"
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        total = data["database"]["total"]

        return DatabaseUsage(
            name=db_info.name,
            storage_used=total["storage_bytes"],
            storage_quota=self.STORAGE_QUOTA_BYTES,
            daily_writes=total["rows_written"],
            daily_quota=self.DAILY_WRITE_QUOTA,
            monthly_writes=db_info.monthly_writes,
            monthly_quota=self.MONTHLY_WRITE_QUOTA,
            last_updated=datetime.now()
        )

    def _store_usage_in_monitoring_db(self, usage: DatabaseUsage):
        """Store usage data in monitoring database"""
        cursor = self.monitoring_db.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO database_usage
            (db_name, storage_used, daily_writes, monthly_writes, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            usage.name,
            usage.storage_used,
            usage.daily_writes,
            usage.monthly_writes,
            usage.last_updated
        ))
        self.monitoring_db.commit()

    def log_write_operation(self, db_name: str, operation_type: str, record_count: int):
        """Log write operations for quota tracking"""
        cursor = self.monitoring_db.cursor()
        cursor.execute('''
            INSERT INTO write_log (db_name, operation_type, record_count)
            VALUES (?, ?, ?)
        ''', (db_name, operation_type, record_count))

        # Update monthly writes
        if db_name in self.databases:
            self.databases[db_name].monthly_writes += record_count

        self.monitoring_db.commit()

    def check_and_create_alerts(self):
        """Check all databases and create alerts for quota issues"""
        alerts = []

        for db_name, db_info in self.databases.items():
            usage = self.get_database_usage(db_name)
            if not usage:
                continue

            storage_pct = (usage.storage_used / usage.storage_quota) * 100
            daily_pct = (usage.daily_writes / usage.daily_quota) * 100
            monthly_pct = (usage.monthly_writes / usage.monthly_quota) * 100

            # Storage alert
            if storage_pct >= 70:
                severity = "CRITICAL" if storage_pct >= 90 else "WARNING"
                alerts.append({
                    "db_name": db_name,
                    "alert_type": "storage",
                    "message": f"Storage usage: {storage_pct:.1f}% ({self._format_bytes(usage.storage_used)})",
                    "severity": severity
                })

            # Daily writes alert
            if daily_pct >= 70:
                severity = "CRITICAL" if daily_pct >= 90 else "WARNING"
                alerts.append({
                    "db_name": db_name,
                    "alert_type": "daily_writes",
                    "message": f"Daily writes: {daily_pct:.1f}% ({usage.daily_writes}/{usage.daily_quota})",
                    "severity": severity
                })

            # Monthly writes alert
            if monthly_pct >= 70:
                severity = "CRITICAL" if monthly_pct >= 90 else "WARNING"
                alerts.append({
                    "db_name": db_name,
                    "alert_type": "monthly_writes",
                    "message": f"Monthly writes: {monthly_pct:.1f}% ({usage.monthly_writes}/{usage.monthly_quota})",
                    "severity": severity
                })

        # Store alerts in database
        cursor = self.monitoring_db.cursor()
        for alert in alerts:
            cursor.execute('''
                INSERT INTO alerts (db_name, alert_type, message, severity)
                VALUES (?, ?, ?, ?)
            ''', (
                alert["db_name"],
                alert["alert_type"],
                alert["message"],
                alert["severity"]
            ))

        self.monitoring_db.commit()
        return alerts

    def _format_bytes(self, size: int) -> str:
        """Convert bytes to human-readable format"""
        size_float = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_float < 1024:
                return f"{size_float:.2f} {unit}"
            size_float /= 1024
        return f"{size_float:.2f} PB"

    def get_all_usage_stats(self) -> List[DatabaseUsage]:
        """Get usage statistics for all databases"""
        stats = []
        for db_name in self.databases.keys():
            usage = self.get_database_usage(db_name)
            if usage:
                stats.append(usage)
        return stats

    def reset_monthly_counters(self):
        """Reset monthly write counters (call on 1st of each month)"""
        for db in self.databases.values():
            db.monthly_writes = 0
            db.last_reset = datetime.now()

        self.save_databases()

        # Clear monthly data from monitoring DB
        cursor = self.monitoring_db.cursor()
        cursor.execute("DELETE FROM write_log WHERE timestamp < date('now', '-30 days')")
        self.monitoring_db.commit()

    def get_active_databases(self) -> List[DatabaseInfo]:
        """Get list of active databases"""
        return [db for db in self.databases.values() if db.is_active]

    def deactivate_database(self, db_name: str):
        """Deactivate a database"""
        if db_name in self.databases:
            self.databases[db_name].is_active = False
            self.save_databases()
            print(f"✅ Deactivated database: {db_name}")

    def activate_database(self, db_name: str):
        """Activate a database"""
        if db_name in self.databases:
            self.databases[db_name].is_active = True
            self.save_databases()
            print(f"✅ Activated database: {db_name}")


# Global instance
_turso_manager = None


def get_turso_manager() -> TursoMultiDatabaseManager:
    """Get the global Turso database manager"""
    global _turso_manager
    if _turso_manager is None:
        _turso_manager = TursoMultiDatabaseManager()
    return _turso_manager


if __name__ == "__main__":
    # Test the multi-database manager
    print("Testing Turso Multi-Database Manager...")

    manager = get_turso_manager()

    # Add a test database (you'll need to replace with real credentials)
    try:
        manager.add_database(
            name="test_db_1",
            url="your-turso-url",
            auth_token="your-auth-token",
            org_slug="your-org-slug"
        )
    except ValueError:
        print("Test database already exists")

    # Get usage stats
    stats = manager.get_all_usage_stats()
    print(f"📊 Found {len(stats)} databases")

    for stat in stats:
        print(f"  {stat.name}: {manager._format_bytes(stat.storage_used)} used")

    # Check for alerts
    alerts = manager.check_and_create_alerts()
    if alerts:
        print(f"🚨 Found {len(alerts)} alerts:")
        for alert in alerts:
            print(f"  {alert['severity']}: {alert['db_name']} - {alert['message']}")
    else:
        print("✅ No alerts found")


class TursoConnection:
    """Turso database connection wrapper that maintains SQLite compatibility"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.use_turso = getattr(config, 'USE_TURSO', False) and TURSO_AVAILABLE
        self._conn: Optional[sqlite3.Connection] = None
        self._turso_client: Any = None

        if self.use_turso:
            self._init_turso_connection()
        else:
            self._init_sqlite_connection()

    def _init_turso_connection(self):
        """Initialize Turso connection"""
        if not TURSO_AVAILABLE or create_client is None:
            print("❌ Turso not available, falling back to SQLite")
            self.use_turso = False
            self._init_sqlite_connection()
            return

        try:
            self._turso_client = create_client(
                url=getattr(config, 'TURSO_DATABASE_URL', ''),
                auth_token=getattr(config, 'TURSO_AUTH_TOKEN', '')
            )
            print("✅ Connected to Turso database")
        except Exception as e:
            print(f"❌ Turso connection failed: {e}")
            print("🔄 Falling back to local SQLite")
            self.use_turso = False
            self._init_sqlite_connection()

    def _init_sqlite_connection(self):
        """Initialize local SQLite connection"""
        db_path = self.db_path or getattr(config, 'LOCAL_DB_PATH', 'website_crawler.db')
        self._conn = sqlite3.connect(db_path)
        # Enable WAL mode for better performance
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        print(f"✅ Connected to local SQLite: {db_path}")

    def execute(self, query: str, params: Optional[tuple] = None) -> Union[sqlite3.Cursor, 'TursoCursor']:
        """Execute SQL query (SQLite-compatible interface)"""
        if self.use_turso and self._turso_client:
            return self._execute_turso(query, params)
        else:
            return self._execute_sqlite(query, params)

    def _execute_turso(self, query: str, params: Optional[tuple] = None) -> 'TursoCursor':
        """Execute query on Turso"""
        if not self._turso_client:
            raise RuntimeError("Turso client not initialized")

        # Convert SQLite-style parameters to Turso format
        if params:
            # Replace ? placeholders with $1, $2, etc.
            param_dict = {}
            for i, param in enumerate(params, 1):
                query = query.replace('?', f'${i}', 1)
                param_dict[f'${i}'] = param

            result = self._turso_client.execute(query, param_dict)
        else:
            result = self._turso_client.execute(query)

        return TursoCursor(result)

    def _execute_sqlite(self, query: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
        """Execute query on SQLite"""
        if not self._conn:
            raise RuntimeError("SQLite connection not initialized")

        cursor = self._conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def executemany(self, query: str, params_list: List[tuple]) -> Union[sqlite3.Cursor, List]:
        """Execute many SQL queries"""
        if self.use_turso and self._turso_client:
            # For Turso, execute each query individually
            results = []
            for params in params_list:
                result = self._execute_turso(query, params)
                results.append(result)
            return results
        else:
            if not self._conn:
                raise RuntimeError("SQLite connection not initialized")
            cursor = self._conn.cursor()
            cursor.executemany(query, params_list)
            return cursor

    def commit(self):
        """Commit transaction"""
        if not self.use_turso and self._conn:
            self._conn.commit()

    def close(self):
        """Close connection"""
        if self.use_turso and self._turso_client:
            # Turso client doesn't need explicit closing
            pass
        elif self._conn:
            self._conn.close()

    @property
    def connection(self):
        """Get the underlying connection object"""
        return self._turso_client if self.use_turso else self._conn


class TursoCursor:
    """Cursor wrapper to maintain SQLite compatibility with Turso results"""

    def __init__(self, turso_result):
        self.result = turso_result
        self._row_index = 0

    def fetchone(self):
        """Fetch one row"""
        if self._row_index < len(self.result.rows):
            row = self.result.rows[self._row_index]
            self._row_index += 1
            return row
        return None

    def fetchall(self):
        """Fetch all rows"""
        remaining_rows = self.result.rows[self._row_index:]
        self._row_index = len(self.result.rows)
        return remaining_rows

    def __iter__(self):
        """Make cursor iterable"""
        return iter(self.result.rows[self._row_index:])

    @property
    def lastrowid(self):
        """Get last inserted row ID (Turso specific)"""
        # Turso doesn't provide this in the same way, return None
        return None

    @property
    def rowcount(self):
        """Get number of affected rows"""
        return len(self.result.rows)

    @property
    def description(self):
        """Get column descriptions"""
        if hasattr(self.result, 'columns'):
            return [(col, None, None, None, None, None, None) for col in self.result.columns]
        return None


def create_connection(db_path: Optional[str] = None) -> TursoConnection:
    """Factory function to create database connection"""
    return TursoConnection(db_path)


# Convenience functions for easy database operations
def get_crawler_db() -> TursoConnection:
    """Get crawler database connection"""
    return create_connection(config.LOCAL_DB_PATH)


def get_backlink_db() -> TursoConnection:
    """Get backlink database connection"""
    return create_connection(config.BACKLINK_DB_PATH)


if __name__ == "__main__":
    # Test the connection
    print("Testing Turso connection...")

    if config.USE_TURSO:
        print("🔗 Using Turso database")
        conn = create_connection()
        try:
            cursor = conn.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"✅ Connection successful: {result}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
        finally:
            conn.close()
    else:
        print("💾 Using local SQLite database")
        print(f"Database path: {config.LOCAL_DB_PATH}")
