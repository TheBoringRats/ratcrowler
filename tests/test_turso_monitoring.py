"""
Test script for Turso Database Monitoring System
Run this to test the monitoring system with sample data
"""

import time
import random
from rat.dashboard import TursoMonitor, DatabaseConfig
from rat.utility import DatabaseRotator


def create_sample_databases():
    """Create sample databases for testing"""
    monitor = TursoMonitor()

    # Sample database configurations
    sample_dbs = [
        {
            "name": "db1",
            "url": "https://db1.turso.io",
            "auth_token": "sample_token_1",
            "monthly_write_limit": 10000000,
            "storage_quota_gb": 5.0
        },
        {
            "name": "db2",
            "url": "https://db2.turso.io",
            "auth_token": "sample_token_2",
            "monthly_write_limit": 10000000,
            "storage_quota_gb": 5.0
        },
        {
            "name": "db3",
            "url": "https://db3.turso.io",
            "auth_token": "sample_token_3",
            "monthly_write_limit": 10000000,
            "storage_quota_gb": 5.0
        }
    ]

    print("📝 Adding sample databases...")
    for db_config in sample_dbs:
        config = DatabaseConfig(**db_config)
        monitor.add_database(config)
        print(f"✅ Added database: {db_config['name']}")

    return monitor


def simulate_usage_data(monitor: TursoMonitor):
    """Simulate usage data for testing"""
    print("\n📊 Simulating usage data...")

    databases = monitor.get_all_databases()

    for db in databases:
        db_name = db['name']

        # Simulate some usage data
        storage_used = random.randint(1000000000, 3000000000)  # 1-3GB
        writes_today = random.randint(10000, 50000)  # 10K-50K writes

        # Store simulated data (this would normally come from Turso API)
        # For testing, we'll just simulate the monthly writes
        monthly_writes = random.randint(100000, 500000)  # 100K-500K monthly
        monitor.update_monthly_writes(db_name, monthly_writes)

        print(f"📈 {db_name}: Simulated {monthly_writes} monthly writes")


def test_rotation_system():
    """Test the database rotation system"""
    print("\n🔄 Testing rotation system...")

    rotator = DatabaseRotator()

    # Test getting available database
    try:
        available_db = rotator.get_next_available_database()
        print(f"✅ Available database: {available_db}")
    except Exception as e:
        print(f"❌ No available database: {e}")
        return

    # Test write recording
    print("📝 Recording write operations...")
    for i in range(10):
        rotator.record_write_operation(available_db, random.randint(1, 100))
        time.sleep(0.1)

    # Check if rotation is needed
    needs_rotation = rotator.should_rotate_database(available_db)
    print(f"🔄 Needs rotation: {needs_rotation}")

    # Get database stats
    stats = rotator.get_database_stats(available_db)
    print(f"📊 Stats: {stats}")


def test_dashboard_data():
    """Test dashboard data generation"""
    print("\n📊 Testing dashboard data...")

    monitor = TursoMonitor()
    dashboard_data = monitor.get_dashboard_data()

    print("📈 Dashboard Summary:")
    print(f"   Total Databases: {dashboard_data['summary']['total_databases']}")
    print(f"   Active: {dashboard_data['summary']['active_databases']}")
    print(f"   Warning: {dashboard_data['summary']['warning_databases']}")
    print(f"   Critical: {dashboard_data['summary']['critical_databases']}")

    print("\n📋 Database Details:")
    for db in dashboard_data['databases']:
        print(f"   {db['name']}: {db['status']} - {db['storage_percent']:.1f}% storage, {db['write_percent']:.1f}% writes")


def run_full_test():
    """Run complete test suite"""
    print("🚀 Starting Turso Database Monitoring Test Suite")
    print("=" * 60)

    try:
        # Create sample databases
        monitor = create_sample_databases()

        # Simulate usage data
        simulate_usage_data(monitor)

        # Test rotation system
        test_rotation_system()

        # Test dashboard data
        test_dashboard_data()

        print("\n✅ All tests completed successfully!")
        print("\n🎯 Next steps:")
        print("   1. Run: python turso_monitoring_dashboard.py")
        print("   2. Open: http://localhost:8000")
        print("   3. Add your real Turso databases")
        print("   4. Integrate rotation into your crawler")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_full_test()
