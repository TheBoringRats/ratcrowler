"""
Quick Turso Setup and Test
Loads configuration from turso_config.json and tests the integration
"""

import json
import os
from rat.turso_monitoring_dashboard import TursoMonitor, DatabaseConfig
from rat.turso_database_adapter import TursoWebsiteCrawlerDatabase, TursoBacklinkDatabase


def load_and_setup_databases():
    """Load database configuration and set up monitoring"""
    print("🚀 Loading Turso Database Configuration")
    print("=" * 50)

    # Check if config file exists
    if not os.path.exists("turso_config.json"):
        print("❌ turso_config.json not found!")
        print("\n📝 Please:")
        print("1. Copy turso_config_template.json to turso_config.json")
        print("2. Edit turso_config.json with your real Turso database details")
        print("3. Run this script again")
        return False

    # Load configuration
    try:
        with open("turso_config.json", "r") as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False

    databases = config_data.get("databases", [])
    if not databases:
        print("❌ No databases found in configuration")
        return False

    print(f"📊 Found {len(databases)} databases in configuration")

    # Set up monitoring
    monitor = TursoMonitor()

    print("\n💾 Setting up databases...")
    for db_config in databases:
        try:
            config = DatabaseConfig(**db_config)
            monitor.add_database(config)
            print(f"✅ Added database: {db_config['name']}")
        except Exception as e:
            print(f"❌ Error adding database {db_config['name']}: {e}")
            return False

    print(f"\n🎉 Successfully configured {len(databases)} databases!")
    return True


def test_database_integration():
    """Test the database integration with sample operations"""
    print("\n🧪 Testing Database Integration")
    print("=" * 40)

    try:
        # Test crawler database
        print("📊 Testing crawler database...")
        crawler_db = TursoWebsiteCrawlerDatabase()
        print(f"✅ Crawler database connected to: {crawler_db.db_adapter.get_current_database_name()}")

        # Test backlinks database
        print("🔗 Testing backlinks database...")
        backlinks_db = TursoBacklinkDatabase()
        print(f"✅ Backlinks database connected to: {backlinks_db.db_adapter.get_current_database_name()}")

        # Test sample operations
        print("\n📝 Testing sample operations...")

        # Create a test session
        session_id = crawler_db.create_crawl_session(
            seed_urls=["https://example.com"],
            config={"test": True}
        )
        print(f"✅ Created test session: {session_id}")

        # Store a test page
        test_page = {
            "url": "https://example.com/test",
            "title": "Test Page",
            "content_text": "This is a test page for Turso integration",
            "content_hash": "test123",
            "word_count": 10,
            "http_status_code": 200
        }

        crawler_db.store_crawled_page(test_page, session_id)
        print("✅ Stored test page")

        # Test backlinks
        backlinks_db.store_backlinks([
            type('Backlink', (), {
                'source_url': 'https://test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'Test Link',
                'domain_authority': 50.0
            })()
        ])
        print("✅ Stored test backlinks")

        # Finish session
        crawler_db.finish_crawl_session(session_id, "completed")
        print("✅ Finished test session")

        print("\n🎉 All integration tests passed!")
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def start_monitoring_dashboard():
    """Start the monitoring dashboard"""
    print("\n📊 Starting Monitoring Dashboard")
    print("=" * 40)

    print("🚀 To start the monitoring dashboard, run:")
    print("   python turso_monitoring_dashboard.py")
    print("\n📈 Then visit: http://localhost:8000")
    print("\n🔍 The dashboard will show:")
    print("   • Real-time database usage")
    print("   • Monthly write counts")
    print("   • Automatic rotation alerts")
    print("   • Database health status")


def show_next_steps():
    """Show next steps for the user"""
    print("\n🎯 Next Steps")
    print("=" * 20)

    print("1. ✅ Configure your Turso databases in turso_config.json")
    print("2. 🔄 Update your crawler code:")
    print("   ")
    print("   # Replace this:")
    print("   from crawlerdb import WebsiteCrawlerDatabase")
    print("   from backlinkdb import BacklinkDatabase")
    print("   ")
    print("   # With this:")
    print("   from turso_database_adapter import TursoWebsiteCrawlerDatabase, TursoBacklinkDatabase")
    print("   ")
    print("3. 📊 Start monitoring: python turso_monitoring_dashboard.py")
    print("4. 🧪 Test with a small crawl to verify rotation")
    print("5. 🚀 Scale up your crawling operations!")

    print("\n💡 Pro Tips:")
    print("   • Monitor the dashboard regularly")
    print("   • Add more databases before existing ones fill up")
    print("   • The system automatically rotates at 85% capacity")
    print("   • Check logs for any connection issues")


def main():
    """Main setup and test function"""
    print("🔧 Turso Database Setup and Test")
    print("=" * 50)

    # Step 1: Load and setup databases
    if not load_and_setup_databases():
        print("\n❌ Setup failed. Please check your configuration.")
        return

    # Step 2: Test integration
    if not test_database_integration():
        print("\n❌ Integration test failed. Please check your database credentials.")
        return

    # Step 3: Show monitoring info
    start_monitoring_dashboard()

    # Step 4: Show next steps
    show_next_steps()

    print("\n🎉 Turso integration is ready!")
    print("Your crawler can now handle millions of writes with automatic database rotation.")


if __name__ == "__main__":
    main()
