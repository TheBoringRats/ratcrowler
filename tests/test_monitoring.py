#!/usr/bin/env python3
"""
Test script for the enhanced RatCrawler monitoring system
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_logging_system():
    """Test the enhanced logging system"""
    print("🧪 Testing Enhanced Logging System...")

    try:
        from rat.logger import log_manager, log_db_operation, log_crawl_start, get_logger

        # Test basic logging
        logger = get_logger("test")
        logger.info("Testing basic logging functionality")

        # Test database operation logging
        log_db_operation("test_insert", "test_db", "test_table", record_count=5, success=True)

        # Test crawler logging
        log_crawl_start("test_session_123", ["https://example.com"], {"test": True})

        # Test log retrieval
        recent_logs = log_manager.get_recent_logs(10)
        print(f"✅ Retrieved {len(recent_logs)} recent logs")

        # Test log statistics
        stats = log_manager.get_log_stats()
        print(f"✅ Log stats: {stats['total_logs']} total logs")

        print("✅ Logging system test passed!")
        return True

    except Exception as e:
        print(f"❌ Logging system test failed: {e}")
        return False

def test_database_monitoring():
    """Test the enhanced database monitoring"""
    print("🧪 Testing Database Monitoring...")

    try:
        from rat.healthcheck import Health
        from rat.dblist import DBList

        health = Health()
        db_list = DBList()

        # Test database listing
        crawler_dbs = db_list.crowldbgrab()
        backlink_dbs = db_list.backlinkdbgrab()

        print(f"✅ Found {len(crawler_dbs)} crawler databases")
        print(f"✅ Found {len(backlink_dbs)} backlink databases")

        # Test health check (if databases are available)
        if crawler_dbs and crawler_dbs[0]:
            db = crawler_dbs[0]
            usage = health.current_limit(db['name'], db['organization'], db['apikey'])
            if usage:
                print(f"✅ Health check successful for {db['name']}")
            else:
                print(f"⚠️ Health check returned no data for {db['name']}")

        print("✅ Database monitoring test passed!")
        return True

    except Exception as e:
        print(f"❌ Database monitoring test failed: {e}")
        return False

def test_dashboard_components():
    """Test dashboard components (without running Streamlit)"""
    print("🧪 Testing Dashboard Components...")

    try:
        from dashboard import DashboardManager

        dashboard = DashboardManager()

        # Test database status retrieval
        db_status = dashboard.get_database_status()
        print(f"✅ Retrieved status for {len(db_status)} databases")

        # Test system stats
        system_stats = dashboard.get_system_stats()
        print(f"✅ System stats: {system_stats['total_logs']} logs")

        # Test log retrieval
        recent_logs = dashboard.get_recent_logs(5)
        print(f"✅ Retrieved {len(recent_logs)} recent logs")

        print("✅ Dashboard components test passed!")
        return True

    except Exception as e:
        print(f"❌ Dashboard components test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🕷️ RatCrawler Enhanced Monitoring System Test")
    print("=" * 50)

    tests = [
        test_logging_system,
        test_database_monitoring,
        test_dashboard_components
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print()

    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The enhanced monitoring system is ready.")
        print("\nTo start the dashboard:")
        print("  python run_dashboard.py")
        print("\nTo run database monitoring:")
        print("  python monitor_databases.py")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
