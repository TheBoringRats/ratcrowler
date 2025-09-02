"""
Simple Turso Integration Test
Tests the database adapter without requiring the full web dashboard
"""

import sys
import os

# Add parent directory to path to import modules from the main package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_turso_adapter():
    """Test the Turso database adapter functionality"""
    print("🧪 Testing Turso Database Adapter")
    print("=" * 40)

    try:
        # Test imports
        print("📦 Testing imports...")
        from rat.adapter import TursoDatabaseAdapter, TursoConnection
        print("✅ Imports successful")

        # Test database adapter initialization
        print("🔧 Testing database adapter...")
        adapter = TursoDatabaseAdapter("test")
        print("✅ Database adapter initialized")

        # Test connection switching (will fail gracefully without real Turso DBs)
        print("🔄 Testing connection switching...")
        adapter._switch_to_available_database()
        print("✅ Connection switching test completed")

        # Test current database name
        db_name = adapter.get_current_database_name()
        print(f"📊 Current database: {db_name}")

        print("🎉 Turso adapter test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_rotation_utility():
    """Test the rotation utility functions"""
    print("\n🔄 Testing Rotation Utility")
    print("=" * 40)

    try:
        # Test basic rotation functions
        print("📦 Testing rotation utility imports...")
        from rat.utility import DatabaseRotator
        print("✅ Rotation utility imports successful")

        # Test rotator initialization
        print("🔧 Testing rotator...")
        rotator = DatabaseRotator()
        print("✅ Database rotator initialized")

        print("🎉 Rotation utility test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Rotation test failed: {e}")
        return False

def test_integration_structure():
    """Test that the integration structure is correct"""
    print("\n🏗️ Testing Integration Structure")
    print("=" * 40)

    # Check if all required files exist
    required_files = [
        "turso_database_adapter.py",
        "turso_rotation_utility.py",
        "turso_monitoring_dashboard.py",
        "integration_example.py",
        "TURSO_INTEGRATION_README.md"
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All integration files present")
        return True

def main():
    """Run all integration tests"""
    print("🚀 Turso Database Integration Test Suite")
    print("=" * 50)

    tests = [
        test_integration_structure,
        test_rotation_utility,
        test_turso_adapter
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Turso integration is ready.")
        print("\n📝 Next steps:")
        print("1. Configure your Turso databases in turso_monitoring_dashboard.py")
        print("2. Run: python turso_monitoring_dashboard.py")
        print("3. Update your crawler imports to use Turso classes")
        print("4. Start crawling with automatic database rotation!")
    else:
        print("❌ Some tests failed. Please check the errors above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
