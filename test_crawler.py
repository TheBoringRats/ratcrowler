#!/usr/bin/env python3
"""
Test script for RatCrawler - runs a small batch without background services
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rat.auto_batch_crawler import AutoBatchCrawler

async def test_crawler():
    """Test the crawler with a small batch"""
    print("🕷️ RatCrawler Test Mode")
    print("=" * 40)
    print("Testing batch crawler functionality...")
    print()

    try:
        # Create crawler with small batch size for testing
        crawler = AutoBatchCrawler(batch_size=5)  # Small batch for testing

        # Check if we have URLs in database
        total_urls = crawler.get_total_backlink_urls_count()
        print(f"📊 Total URLs in database: {total_urls:,}")

        if total_urls == 0:
            print("❌ No URLs found in database. Please add some URLs first.")
            return False

        # Get a small sample batch
        sample_urls = crawler.get_backlink_urls_batch(1, 5)
        print(f"📦 Sample batch: {len(sample_urls)} URLs")

        for i, url in enumerate(sample_urls[:3], 1):
            print(f"   {i}. {url}")

        if len(sample_urls) > 3:
            print(f"   ... and {len(sample_urls) - 3} more URLs")

        print()
        print("✅ Crawler setup successful!")
        print("🎯 Ready for full crawling with: python main.py")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running RatCrawler test...")
    success = asyncio.run(test_crawler())

    if success:
        print("\n🎉 Test completed successfully!")
        print("💡 To run full crawler: python main.py")
        print("🌐 To access dashboard: streamlit run dashboard.py")
    else:
        print("\n❌ Test failed. Please check the error messages above.")
