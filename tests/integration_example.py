"""
Integration Example: How to use Turso databases in your existing crawler
This shows how to seamlessly replace your SQLite databases with Turso
"""

# Example 1: Replace your existing database imports
print("🔄 Integration Example 1: Database Replacement")
print("=" * 50)

# OLD WAY (SQLite):
# from crawlerdb import WebsiteCrawlerDatabase
# from backlinkdb import BacklinkDatabase

# NEW WAY (Turso with automatic rotation):
from rat.turso_database_adapter import TursoWebsiteCrawlerDatabase, TursoBacklinkDatabase

# Your existing crawler code stays almost the same!
def example_crawler_usage():
    """Example of how your crawler code will work with Turso"""

    # Initialize databases (drop-in replacement)
    crawler_db = TursoWebsiteCrawlerDatabase()  # Instead of WebsiteCrawlerDatabase()
    backlinks_db = TursoBacklinkDatabase()       # Instead of BacklinkDatabase()

    print(f"📊 Crawler database: {crawler_db.db_adapter.get_current_database_name()}")
    print(f"🔗 Backlinks database: {backlinks_db.db_adapter.get_current_database_name()}")

    # Create crawl session (same API as before)
    session_id = crawler_db.create_crawl_session(
        seed_urls=["https://example.com"],
        config={"max_depth": 3, "delay": 1}
    )
    print(f"🎯 Created session: {session_id}")

    # Store crawled page (same API)
    page_data = {
        "url": "https://example.com/page1",
        "title": "Example Page",
        "content_text": "This is sample content...",
        "content_hash": "abc123",
        "word_count": 150,
        "http_status_code": 200
    }

    crawler_db.store_crawled_page(page_data, session_id)
    print("✅ Page stored in Turso database")

    # Store backlinks (same API)
    backlinks_db.store_backlinks([
        type('Backlink', (), {
            'source_url': 'https://referrer.com',
            'target_url': 'https://example.com',
            'anchor_text': 'Example Link',
            'domain_authority': 85.5
        })()
    ])
    print("✅ Backlinks stored in Turso database")

    # Finish session
    crawler_db.finish_crawl_session(session_id, "completed")
    print("🎉 Crawl session completed")

# Example 2: Migration from existing SQLite data
def example_migration():
    """Example of migrating existing data to Turso"""
    print("\n🔄 Integration Example 2: Data Migration")
    print("=" * 50)

    from rat.turso_database_adapter import migrate_to_turso

    # One-time migration of existing SQLite data to Turso
    success = migrate_to_turso()

    if success:
        print("✅ Migration successful!")
        print("🔄 Your crawler now uses Turso databases with automatic rotation")
    else:
        print("❌ Migration failed - check your database configurations")

# Example 3: Monitoring and rotation in action
def example_monitoring():
    """Example of monitoring database usage and rotation"""
    print("\n📊 Integration Example 3: Monitoring & Rotation")
    print("=" * 50)

    from rat.turso_rotation_utility import check_database_health, get_current_database

    # Check current database status
    current_db = get_current_database()
    print(f"🎯 Current active database: {current_db}")

    # Get usage statistics
    health_stats = check_database_health()
    for db_name, stats in health_stats.items():
        print(f"📈 {db_name}: {stats.get('monthly_writes', 0)}/{stats.get('write_limit', 0)} writes this month")

    print("\n🔄 Automatic rotation will happen when databases approach 10M monthly writes")
    print("📊 Monitor via: http://localhost:8000 (when you run the monitoring dashboard)")

if __name__ == "__main__":
    print("🚀 Turso Database Integration Examples")
    print("=" * 60)

    try:
        example_crawler_usage()
        example_migration()
        example_monitoring()

        print("\n🎉 Integration examples completed!")
        print("\n📝 Next steps:")
        print("1. Update your crawler imports to use Turso classes")
        print("2. Run the monitoring dashboard: python turso_monitoring_dashboard.py")
        print("3. Start crawling with automatic database rotation!")

    except Exception as e:
        print(f"❌ Example failed: {e}")
        print("💡 Make sure your Turso databases are configured in turso_monitoring_dashboard.py")
