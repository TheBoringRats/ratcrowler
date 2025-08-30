"""
Turso Database Rotation Utility
Integrate this into your crawler to automatically rotate between databases
"""

from rat.dashboard import TursoMonitor
import time
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from typing import Optional, Dict


class DatabaseRotator:
    """Handles automatic database rotation based on capacity"""

    def __init__(self):
        self.monitor = TursoMonitor()
        self.current_db = None
        # Cache SQLAlchemy engines by db name
        self._engine_cache: Dict[str, Engine] = {}

    def get_next_available_database(self) -> str:
        """Get the next available database for writing"""
        available_db = self.monitor.get_available_database()
        if available_db:
            self.current_db = available_db
            return available_db
        else:
            raise Exception("No available databases with capacity")

    def get_engine_for_db(self, db_name: str) -> Optional[Engine]:
        """Return a SQLAlchemy Engine for the given database name (caches engines).

        Uses the monitor's stored URL and auth token to construct a SQLite SQLAlchemy URL
        if the monitored config contains a Turso URL. Returns None if config missing.
        """
        if db_name in self._engine_cache:
            return self._engine_cache[db_name]

        dbs = self.monitor.get_all_databases()
        cfg = next((d for d in dbs if d['name'] == db_name), None)
        if not cfg:
            return None

        url = cfg.get('url')
        auth = cfg.get('auth_token')

        if not url:
            return None

        # Build SQLite SQLAlchemy URL for Turso: sqlite+<url>?secure=true
        if auth:
            db_url = f"sqlite+{url}?secure=true"
        else:
            db_url = f"sqlite+{url}"

        try:
            connect_args = {}
            if auth:
                connect_args = {"auth_token": auth}
            engine = create_engine(db_url, future=True, connect_args=connect_args)
            self._engine_cache[db_name] = engine
            return engine
        except Exception as e:
            print(f"❌ Failed to create engine for {db_name}: {e}")
            return None

    def record_write_operation(self, db_name: str, write_count: int = 1):
        """Record write operations for tracking monthly limits"""
        self.monitor.update_monthly_writes(db_name, write_count)

    def should_rotate_database(self, db_name: str) -> bool:
        """Check if database needs rotation"""
        usage = self.monitor.get_database_usage(db_name)
        monthly_writes = self.monitor.get_monthly_writes(db_name)

        # Rotate if approaching 90% capacity
        storage_percent = (usage.get('storage_used', 0) / usage.get('storage_quota', 1)) * 100
        write_limit = self.monitor.databases[db_name].monthly_write_limit
        write_percent = (monthly_writes / write_limit) * 100 if write_limit > 0 else 0

        return storage_percent >= 85 or write_percent >= 85

    def get_database_stats(self, db_name: str) -> dict:
        """Get comprehensive stats for a database"""
        usage = self.monitor.get_database_usage(db_name)
        monthly_writes = self.monitor.get_monthly_writes(db_name)

        return {
            'name': db_name,
            'storage_used': usage.get('storage_used', 0),
            'storage_quota': usage.get('storage_quota', 0),
            'monthly_writes': monthly_writes,
            'write_limit': self.monitor.databases[db_name].monthly_write_limit,
            'needs_rotation': self.should_rotate_database(db_name)
        }


# Global rotator instance
rotator = DatabaseRotator()


def get_current_database():
    """Get current database for writing"""
    if rotator.current_db and not rotator.should_rotate_database(rotator.current_db):
        return rotator.current_db
    else:
        return rotator.get_next_available_database()


def get_current_engine() -> Optional[Engine]:
    """Return a SQLAlchemy Engine for the current database (or None)."""
    db_name = None
    try:
        db_name = get_current_database()
    except Exception:
        return None

    if not db_name:
        return None

    return rotator.get_engine_for_db(db_name)


def record_writes(db_name: str, count: int = 1):
    """Record write operations"""
    rotator.record_write_operation(db_name, count)


def check_database_health():
    """Check health of all databases"""
    databases = rotator.monitor.get_all_databases()
    health_status = {}

    for db in databases:
        db_name = db['name']
        stats = rotator.get_database_stats(db_name)
        health_status[db_name] = stats

    return health_status


# Example integration with your crawler
class TursoIntegratedCrawler:
    """Example of how to integrate Turso rotation with your crawler"""

    def __init__(self):
        self.current_db = None

    def get_database_connection(self):
        """Get appropriate database connection with rotation"""
        try:
            db_name = get_current_database()
            if db_name != self.current_db:
                print(f"🔄 Rotated to database: {db_name}")
                self.current_db = db_name

            # Here you would return actual database connection
            # For now, just return the database name
            return db_name

        except Exception as e:
            print(f"❌ No available databases: {e}")
            return None

    def perform_write_operation(self, data):
        """Perform write operation with automatic rotation"""
        db_name = self.get_database_connection()
        if not db_name:
            raise Exception("No available database for writing")

        try:
            # Your actual write operation here
            # For example: insert data into Turso database
            print(f"📝 Writing to database: {db_name}")

            # Record the write operation
            record_writes(db_name, 1)  # Record 1 write

            return True

        except Exception as e:
            print(f"❌ Write failed: {e}")
            return False

    def perform_bulk_write(self, data_list):
        """Perform bulk write with rotation"""
        successful_writes = 0

        for data in data_list:
            if self.perform_write_operation(data):
                successful_writes += 1
            else:
                # If write fails, try rotating to another database
                self.current_db = None  # Force rotation
                if self.perform_write_operation(data):
                    successful_writes += 1

        return successful_writes


# Example usage
if __name__ == "__main__":
    print("🚀 Turso Database Rotation System")
    print("=" * 50)

    # Initialize crawler
    crawler = TursoIntegratedCrawler()

    # Simulate some write operations
    test_data = [f"data_{i}" for i in range(10)]

    print("Performing bulk write operations...")
    successful = crawler.perform_bulk_write(test_data)
    print(f"✅ Successfully wrote {successful}/{len(test_data)} items")

    # Check database health
    print("\n📊 Database Health Status:")
    health = check_database_health()
    for db_name, stats in health.items():
        print(f"  {db_name}: {stats['monthly_writes']}/{stats['write_limit']} writes, {stats['needs_rotation'] and 'NEEDS ROTATION' or 'OK'}")
