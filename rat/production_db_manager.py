"""
Production Database Manager for Live Applications
Handles connection pooling, health monitoring, and safe updates.
"""

import sqlite3
import threading
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Union
from contextlib import contextmanager
from rat.config import config


class ProductionDatabaseManager:
    """Thread-safe database manager for production use"""

    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self.connections = {}
        self.connection_lock = threading.Lock()
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = 0

        # Initialize connection pool
        self._init_connection_pool()

    def _init_connection_pool(self):
        """Initialize database connection pool"""
        with self.connection_lock:
            for i in range(self.max_connections):
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
                conn.execute("PRAGMA synchronous=NORMAL")  # Balance between performance and safety
                conn.execute("PRAGMA cache_size=10000")  # 10MB cache
                conn.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
                self.connections[i] = {
                    'connection': conn,
                    'in_use': False,
                    'last_used': time.time()
                }

    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        conn_id = None
        conn_info = None

        # Find available connection
        with self.connection_lock:
            for cid, info in self.connections.items():
                if not info['in_use']:
                    conn_id = cid
                    conn_info = info
                    info['in_use'] = True
                    info['last_used'] = time.time()
                    break

        if conn_id is None or conn_info is None:
            raise RuntimeError("No available database connections")

        try:
            yield conn_info['connection']
        finally:
            with self.connection_lock:
                if conn_id in self.connections:
                    self.connections[conn_id]['in_use'] = False

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Execute a SELECT query safely"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Return results as list of dictionaries
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query safely"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute multiple INSERT/UPDATE queries efficiently"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        current_time = time.time()

        # Only check health periodically
        if current_time - self.last_health_check < self.health_check_interval:
            return {"status": "cached", "last_check": self.last_health_check}

        self.last_health_check = current_time

        try:
            # Test basic connectivity
            result = self.execute_query("SELECT 1 as test")
            if result and result[0]['test'] == 1:
                status = "healthy"
            else:
                status = "unhealthy"

            # Get database statistics
            stats = self.execute_query("""
                SELECT
                    name as table_name,
                    sql as table_definition
                FROM sqlite_master
                WHERE type='table'
            """)

            # Check connection pool status
            pool_status = {}
            with self.connection_lock:
                for cid, info in self.connections.items():
                    pool_status[f"conn_{cid}"] = {
                        "in_use": info['in_use'],
                        "last_used_seconds_ago": current_time - info['last_used']
                    }

            return {
                "status": status,
                "timestamp": current_time,
                "tables_count": len(stats),
                "connection_pool": pool_status
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": current_time
            }

    def optimize_for_live_updates(self):
        """Optimize database for frequent live updates"""
        with self.get_connection() as conn:
            # Enable WAL mode for better write performance
            conn.execute("PRAGMA journal_mode=WAL")

            # Optimize synchronous mode for balance
            conn.execute("PRAGMA synchronous=NORMAL")

            # Increase cache size for better performance
            conn.execute("PRAGMA cache_size=20000")  # 20MB cache

            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys=ON")

            print("🔧 Database optimized for live updates")

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Create a live backup without stopping the application"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.live_backup_{timestamp}"

        try:
            with self.get_connection() as source_conn:
                with sqlite3.connect(backup_path) as backup_conn:
                    source_conn.backup(backup_conn)

            print(f"📦 Live backup created: {backup_path}")
            return backup_path

        except Exception as e:
            print(f"❌ Backup failed: {e}")
            raise

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        metrics = {}

        try:
            # Get database file size
            if os.path.exists(self.db_path):
                metrics['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)

            # Get table statistics
            tables_stats = self.execute_query("""
                SELECT
                    name,
                    (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=t.name) as index_count
                FROM sqlite_master t
                WHERE type='table'
            """)

            metrics['tables'] = {row['name']: row['index_count'] for row in tables_stats}

            # Get connection pool metrics
            with self.connection_lock:
                in_use_count = sum(1 for info in self.connections.values() if info['in_use'])
                metrics['connection_pool'] = {
                    'total_connections': len(self.connections),
                    'in_use': in_use_count,
                    'available': len(self.connections) - in_use_count
                }

        except Exception as e:
            metrics['error'] = str(e)

        return metrics

    def close_all_connections(self):
        """Close all database connections"""
        with self.connection_lock:
            for conn_info in self.connections.values():
                try:
                    conn_info['connection'].close()
                except Exception as e:
                    print(f"Warning: Error closing connection: {e}")

            self.connections.clear()


# Global database manager instance
_db_manager = None
_db_lock = threading.Lock()


def get_database_manager(db_path: str = "website_crawler.db") -> ProductionDatabaseManager:
    """Get or create the global database manager instance"""
    global _db_manager

    if _db_manager is None:
        with _db_lock:
            if _db_manager is None:  # Double-check locking
                _db_manager = ProductionDatabaseManager(db_path)

    return _db_manager


# Convenience functions for easy use
def db_query(query: str, params: Optional[Tuple] = None) -> List[Dict]:
    """Execute a database query"""
    return get_database_manager().execute_query(query, params)


def db_update(query: str, params: Optional[Tuple] = None) -> int:
    """Execute a database update"""
    return get_database_manager().execute_update(query, params)


def db_health_check() -> Dict[str, Any]:
    """Check database health"""
    return get_database_manager().health_check()


if __name__ == "__main__":
    # Example usage
    db_manager = get_database_manager()

    # Health check
    health = db_health_check()
    print("🏥 Database Health:", health)

    # Performance metrics
    metrics = db_manager.get_performance_metrics()
    print("📊 Performance Metrics:", metrics)

    # Example query
    try:
        results = db_query("SELECT COUNT(*) as total_pages FROM crawled_pages")
        print(f"📄 Total crawled pages: {results[0]['total_pages'] if results else 0}")
    except Exception as e:
        print(f"Query failed: {e}")
