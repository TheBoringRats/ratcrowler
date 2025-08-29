"""
Live Database Integration Example
Shows how to integrate production database management into your crawler.
"""

from rat.production_db_manager import get_database_manager, db_query, db_update
from database_migration import run_pending_migrations
from rat.crawler import EnhancedProductionCrawler
import time
import threading


class LiveCrawlerWithDatabase:
    """Enhanced crawler with live database management"""

    def __init__(self, config: dict):
        self.config = config
        self.db_path = config.get('db_path', 'website_crawler.db')

        # Initialize production database manager
        self.db_manager = get_database_manager(self.db_path)

        # Run any pending migrations
        run_pending_migrations(self.db_path)

        # Initialize the crawler
        self.crawler = EnhancedProductionCrawler(config)

        # Start background tasks
        self.start_background_tasks()

    def start_background_tasks(self):
        """Start background database maintenance tasks"""

        def database_maintenance():
            """Periodic database maintenance"""
            while True:
                try:
                    # Health check
                    health = self.db_manager.health_check()
                    if health['status'] != 'healthy':
                        print(f"⚠️ Database health issue: {health}")

                    # Optimize database periodically
                    if time.time() % 3600 < 60:  # Every hour
                        self.db_manager.optimize_for_live_updates()

                    # Update crawler metrics
                    self.update_crawler_metrics()

                except Exception as e:
                    print(f"Database maintenance error: {e}")

                time.sleep(300)  # Check every 5 minutes

        def backup_task():
            """Periodic backup task"""
            while True:
                try:
                    # Create backup daily
                    if time.time() % 86400 < 60:  # Every 24 hours
                        backup_path = self.db_manager.backup_database()
                        print(f"✅ Daily backup completed: {backup_path}")

                except Exception as e:
                    print(f"Backup task error: {e}")

                time.sleep(3600)  # Check every hour

        # Start background threads
        threading.Thread(target=database_maintenance, daemon=True).start()
        threading.Thread(target=backup_task, daemon=True).start()

    def update_crawler_metrics(self):
        """Update crawler performance metrics in database"""
        try:
            # Get current stats
            stats = self.db_manager.get_performance_metrics()

            # Insert metrics
            db_update("""
                INSERT INTO crawler_metrics
                (pages_crawled, backlinks_found, errors_count, avg_response_time)
                VALUES (?, ?, ?, ?)
            """, (
                stats.get('tables', {}).get('crawled_pages', 0),
                stats.get('tables', {}).get('backlinks', 0),
                0,  # You can track errors separately
                0.0  # You can calculate average response time
            ))

        except Exception as e:
            print(f"Metrics update error: {e}")

    def crawl_with_live_updates(self, urls: list):
        """Crawl URLs with live database updates"""
        print("🚀 Starting live crawl with database management...")

        # Optimize database for bulk operations
        self.db_manager.optimize_for_live_updates()

        # Start crawling
        results = self.crawler.comprehensive_crawl(urls)

        # Get session ID from results or create one
        session_id = results.get('session_id', 1)  # Default to 1 if not available

        # Update final statistics
        self.update_progress_in_db(session_id, {
            'pages_crawled': len(results.get('crawled_pages', [])),
            'avg_response_time': 0,  # Calculate if available
            'errors': 0
        })

        print("✅ Crawl completed with live database updates")
        return results

    def get_crawler_progress(self, session_id: int) -> dict:
        """Get current crawler progress"""
        try:
            results = db_query("""
                SELECT
                    COUNT(*) as pages_crawled,
                    AVG(response_time_ms) as avg_response_time,
                    SUM(CASE WHEN http_status_code >= 400 THEN 1 ELSE 0 END) as errors
                FROM crawled_pages
                WHERE session_id = ?
            """, (session_id,))

            if results:
                return results[0]
            return {}

        except Exception as e:
            print(f"Progress query error: {e}")
            return {}

    def update_progress_in_db(self, session_id: int, progress: dict):
        """Update crawl progress in database"""
        try:
            db_update("""
                UPDATE crawl_sessions
                SET pages_crawled = ?, avg_response_time = ?, errors_count = ?
                WHERE id = ?
            """, (
                progress.get('pages_crawled', 0),
                progress.get('avg_response_time', 0),
                progress.get('errors', 0),
                session_id
            ))
        except Exception as e:
            print(f"Progress update error: {e}")

    def get_database_stats(self) -> dict:
        """Get comprehensive database statistics"""
        try:
            # Get basic stats
            stats = self.db_manager.get_performance_metrics()

            # Get crawler-specific stats
            crawler_stats = db_query("""
                SELECT
                    COUNT(DISTINCT url) as unique_urls,
                    COUNT(*) as total_pages,
                    AVG(word_count) as avg_word_count,
                    COUNT(DISTINCT session_id) as crawl_sessions
                FROM crawled_pages
            """)

            if crawler_stats:
                stats.update(crawler_stats[0])

            # Get health status
            stats['health'] = self.db_manager.health_check()

            return stats

        except Exception as e:
            return {'error': str(e)}


def example_live_crawler():
    """Example of using the live crawler"""

    # Configuration
    config = {
        'delay': 1.5,
        'max_depth': 3,
        'max_pages': 100,
        'db_path': 'website_crawler.db',
        'user_agent': 'LiveCrawler/1.0'
    }

    # Initialize live crawler
    live_crawler = LiveCrawlerWithDatabase(config)

    # Example URLs to crawl
    urls = [
        "https://example.com",
        "https://github.com",
        "https://python.org"
    ]

    # Start crawling with live database updates
    live_crawler.crawl_with_live_updates(urls)

    # Get final statistics
    stats = live_crawler.get_database_stats()
    print("📊 Final Database Stats:", stats)


if __name__ == "__main__":
    example_live_crawler()
