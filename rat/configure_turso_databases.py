"""
Turso Database Configuration Helper
Helps you set up your Turso databases for the crawler integration
"""

import os
import json
from rat.turso_monitoring_dashboard import TursoMonitor, DatabaseConfig


def configure_turso_databases():
    """Interactive setup for Turso databases"""

    print("🚀 Turso Database Configuration")
    print("=" * 50)
    print("Let's set up your Turso databases for automatic rotation.")
    print("You'll need your Turso database URLs and auth tokens.\n")

    monitor = TursoMonitor()

    # Get number of databases
    while True:
        try:
            num_dbs = int(input("How many Turso databases do you want to configure? (2-20): "))
            if 2 <= num_dbs <= 20:
                break
            else:
                print("Please enter a number between 2 and 20.")
        except ValueError:
            print("Please enter a valid number.")

    databases = []

    for i in range(num_dbs):
        print(f"\n📊 Database {i+1}/{num_dbs}")
        print("-" * 30)

        # Database name
        name = input(f"Database name (e.g., crawler_db_{i+1}): ").strip()
        if not name:
            name = f"crawler_db_{i+1}"

        # Database URL
        while True:
            url = input("Turso database URL (e.g., https://your-db.turso.io): ").strip()
            if url.startswith("https://") and "turso.io" in url:
                break
            else:
                print("Please enter a valid Turso URL (should start with https:// and contain turso.io)")

        # Auth token
        auth_token = input("Auth token (from Turso dashboard): ").strip()
        if not auth_token:
            print("⚠️  Warning: Empty auth token provided")

        # Monthly write limit
        while True:
            try:
                limit_input = input("Monthly write limit (default 10000000 = 10M): ").strip()
                monthly_limit = int(limit_input) if limit_input else 10000000
                break
            except ValueError:
                print("Please enter a valid number.")

        # Storage quota
        while True:
            try:
                quota_input = input("Storage quota in GB (default 5.0): ").strip()
                storage_quota = float(quota_input) if quota_input else 5.0
                break
            except ValueError:
                print("Please enter a valid number.")

        # Create configuration
        config = DatabaseConfig(
            name=name,
            url=url,
            auth_token=auth_token,
            monthly_write_limit=monthly_limit,
            storage_quota_gb=storage_quota
        )

        databases.append(config)
        print(f"✅ Database {name} configured")

    # Save configuration
    print("\n💾 Saving configuration...")
    for config in databases:
        monitor.add_database(config)

    # Save to JSON file for backup
    config_data = {
        "databases": [
            {
                "name": db.name,
                "url": db.url,
                "auth_token": db.auth_token,
                "monthly_write_limit": db.monthly_write_limit,
                "storage_quota_gb": db.storage_quota_gb
            } for db in databases
        ]
    }

    with open("turso_config.json", "w") as f:
        json.dump(config_data, f, indent=2)

    print("✅ Configuration saved to turso_config.json")

    # Summary
    print("\n🎉 Configuration Complete!")
    print("=" * 50)
    print(f"✅ {len(databases)} databases configured")
    print("\n📊 Database Summary:")
    for db in databases:
        print(f"  • {db.name}: {db.url}")

    print("\n🔄 Next steps:")
    print("1. Start the monitoring dashboard: python turso_monitoring_dashboard.py")
    print("2. Visit http://localhost:8000 to monitor your databases")
    print("3. Update your crawler code to use Turso databases")
    print("4. Test with a small crawl to verify rotation works")

    return databases


def load_existing_config():
    """Load existing configuration from JSON file"""
    if os.path.exists("turso_config.json"):
        print("📂 Found existing configuration file")
        with open("turso_config.json", "r") as f:
            data = json.load(f)

        monitor = TursoMonitor()
        for db_config in data["databases"]:
            config = DatabaseConfig(**db_config)
            monitor.add_database(config)

        print(f"✅ Loaded {len(data['databases'])} databases from configuration")
        return True
    return False


def test_database_connections():
    """Test connections to configured databases"""
    print("\n🧪 Testing Database Connections")
    print("=" * 40)

    monitor = TursoMonitor()
    databases = monitor.get_all_databases()

    if not databases:
        print("❌ No databases configured. Run configuration first.")
        return False

    success_count = 0

    for db in databases:
        print(f"Testing {db['name']}...")
        try:
            # Test basic connection (this will be implemented in the monitor)
            usage = monitor.get_database_usage(db['name'])
            if usage:
                print(f"✅ {db['name']}: Connected successfully")
                success_count += 1
            else:
                print(f"⚠️  {db['name']}: Connected but no usage data")
                success_count += 1
        except Exception as e:
            print(f"❌ {db['name']}: Connection failed - {e}")

    print(f"\n📊 Connection Test Results: {success_count}/{len(databases)} successful")

    if success_count == len(databases):
        print("🎉 All databases connected successfully!")
        return True
    else:
        print("⚠️  Some databases failed to connect. Check your URLs and auth tokens.")
        return False


def main():
    """Main configuration menu"""
    print("🔧 Turso Database Configuration Tool")
    print("=" * 50)

    # Check for existing configuration
    if load_existing_config():
        choice = input("Found existing configuration. Use it? (y/n): ").lower()
        if choice == 'y':
            if test_database_connections():
                print("\n✅ Ready to proceed with existing configuration!")
                return
        else:
            print("Creating new configuration...")

    # Configure new databases
    databases = configure_turso_databases()

    # Test connections
    if test_database_connections():
        print("\n🎉 Setup complete! Your Turso databases are ready for the crawler.")
        print("\n🚀 To start using:")
        print("1. python turso_monitoring_dashboard.py")
        print("2. Update your crawler imports")
        print("3. Start crawling with automatic rotation!")
    else:
        print("\n⚠️  Please check your database configurations and try again.")


if __name__ == "__main__":
    main()
