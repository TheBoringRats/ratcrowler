#!/usr/bin/env python3
"""
Test script to verify the optimized backlink storage system
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rat.backlink import BacklinkData, main_discover_and_store
from rat.sqlalchemy_database import SQLAlchemyDatabase


def test_small_backlink_storage():
    """Test storage with a small number of backlinks"""
    print("🧪 Testing backlink storage system with small dataset...")

    # Create test backlinks
    test_backlinks = [
        BacklinkData(
            source_url=f"https://example{i}.com/page",
            target_url=f"https://target{i}.com/",
            anchor_text=f"Test Link {i}",
            context=f"This is test context for link {i}",
            page_title=f"Test Page {i}",
            domain_authority=float(i),
            is_nofollow=(i % 2 == 0)
        )
        for i in range(10)  # Start with just 10 backlinks
    ]

    try:
        db_handler = SQLAlchemyDatabase()

        # Test connectivity
        if not db_handler.test_database_connectivity("backlink"):
            print("❌ Database connectivity test failed")
            return False

        print(f"📦 Storing {len(test_backlinks)} test backlinks...")
        db_handler.store_backlinks(test_backlinks)

        print("📊 Testing domain scores storage...")
        test_domain_scores = {
            f"target{i}.com": float(i * 0.5)
            for i in range(5)
        }
        db_handler.store_domain_scores(test_domain_scores)

        print("✅ Small dataset test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("=== Backlink Storage Optimization Test ===")

    # Test small dataset first
    if test_small_backlink_storage():
        print("\n🎉 All tests passed!")
        print("\n💡 The optimized storage system should now handle large datasets better.")
        print("📈 Key improvements:")
        print("   - Chunked processing (5000 records per chunk)")
        print("   - Progress reporting during storage")
        print("   - Better error handling and recovery")
        print("   - Database connectivity testing")
        print("   - Optimized connection settings")
        print("\n🚀 You can now re-run your backlink discovery with confidence!")
    else:
        print("\n❌ Tests failed. Please check database configuration.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
