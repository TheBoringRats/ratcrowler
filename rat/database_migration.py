"""
Database Migration System for Live Applications
Handles schema updates and data migrations safely in production.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any
from rat.config import config


class DatabaseMigration:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migration_table = "schema_migrations"
        self.init_migration_table()

    def init_migration_table(self):
        """Initialize migration tracking table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.migration_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT
                )
            ''')

    def apply_migration(self, migration_name: str, sql_script: str) -> bool:
        """Apply a migration safely with rollback capability"""
        try:
            # Create backup before migration
            if config.ENABLE_AUTO_BACKUP:
                self.create_backup()

            with sqlite3.connect(self.db_path) as conn:
                # Start transaction
                conn.execute('BEGIN TRANSACTION')

                # Execute migration
                conn.executescript(sql_script)

                # Record migration
                conn.execute(f'''
                    INSERT INTO {self.migration_table} (migration_name)
                    VALUES (?)
                ''', (migration_name,))

                # Commit transaction
                conn.commit()

                print(f"✅ Migration '{migration_name}' applied successfully")
                return True

        except Exception as e:
            print(f"❌ Migration '{migration_name}' failed: {e}")
            # Transaction will auto-rollback on exception
            return False

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f'SELECT migration_name FROM {self.migration_table} ORDER BY id')
            return [row[0] for row in cursor.fetchall()]

    def create_backup(self):
        """Create database backup before migration"""
        if not os.path.exists(self.db_path):
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_path}.backup_{timestamp}"

        # SQLite backup
        with sqlite3.connect(self.db_path) as source:
            with sqlite3.connect(backup_path) as dest:
                source.backup(dest)

        print(f"📦 Backup created: {backup_path}")

        # Clean old backups
        self.clean_old_backups()

    def clean_old_backups(self):
        """Remove backups older than retention period"""
        import glob
        from datetime import timedelta

        backup_pattern = f"{self.db_path}.backup_*"
        retention_date = datetime.now() - timedelta(days=config.BACKUP_RETENTION_DAYS)

        for backup_file in glob.glob(backup_pattern):
            try:
                # Extract timestamp from filename
                timestamp_str = backup_file.split('_')[-1]
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if file_date < retention_date:
                    os.remove(backup_file)
                    print(f"🗑️ Removed old backup: {backup_file}")
            except (ValueError, OSError) as e:
                print(f"Warning: Could not process backup {backup_file}: {e}")


class LiveDatabaseManager:
    """Manages database operations for live applications"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migration_manager = DatabaseMigration(db_path)

    def update_schema_safely(self, new_columns: Dict[str, str]):
        """Add new columns to existing tables safely"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for table_name, columns_sql in new_columns.items():
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone():
                    # Add columns that don't exist
                    for column_sql in columns_sql.split(','):
                        column_sql = column_sql.strip()
                        if column_sql:
                            try:
                                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")
                                print(f"✅ Added column to {table_name}: {column_sql}")
                            except sqlite3.OperationalError as e:
                                if "duplicate column name" not in str(e):
                                    print(f"Warning: Could not add column {column_sql}: {e}")

    def optimize_database(self):
        """Optimize database performance for live operations"""
        with sqlite3.connect(self.db_path) as conn:
            # Run optimization commands
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
            print("🔧 Database optimized")

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get table sizes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                stats[table_name] = count

        return stats


# Example migration scripts
MIGRATIONS = {
    "add_content_index": """
        CREATE INDEX IF NOT EXISTS idx_content_hash ON crawled_pages(content_hash);
        CREATE INDEX IF NOT EXISTS idx_url ON crawled_pages(url);
        CREATE INDEX IF NOT EXISTS idx_crawl_time ON crawled_pages(crawl_time);
    """,

    "add_domain_authority_table": """
        CREATE TABLE IF NOT EXISTS domain_authority (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            authority_score REAL DEFAULT 0.0,
            backlinks_count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,

    "add_crawler_metrics": """
        CREATE TABLE IF NOT EXISTS crawler_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pages_crawled INTEGER DEFAULT 0,
            backlinks_found INTEGER DEFAULT 0,
            errors_count INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0.0
        );
    """
}


def run_pending_migrations(db_path: str):
    """Apply all pending migrations"""
    manager = DatabaseMigration(db_path)
    applied = manager.get_applied_migrations()

    for migration_name, sql_script in MIGRATIONS.items():
        if migration_name not in applied:
            success = manager.apply_migration(migration_name, sql_script)
            if not success:
                print(f"❌ Critical: Migration '{migration_name}' failed. Manual intervention required.")
                break


if __name__ == "__main__":
    # Example usage
    db_path = "website_crawler.db"
    run_pending_migrations(db_path)

    # Live database management
    live_manager = LiveDatabaseManager(db_path)

    # Add new columns safely
    new_columns = {
        "crawled_pages": "crawl_priority INTEGER DEFAULT 1, last_modified TIMESTAMP"
    }
    live_manager.update_schema_safely(new_columns)

    # Get stats
    stats = live_manager.get_database_stats()
    print("📊 Database Stats:", stats)
