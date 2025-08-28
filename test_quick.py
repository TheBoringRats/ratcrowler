#!/usr/bin/env python3
"""
Quick test script for RatCrawler components.
Run this to test the crawler without the scheduling functionality.
"""

from crawler import EnhancedProductionCrawler
import json

def test_crawler():
    """Test the crawler with a simple configuration."""
    print("🧪 Testing RatCrawler Components")
    print("=" * 40)

    # Simple test configuration
    config = {
        'delay': 1.0,
        'max_depth': 2,
        'max_pages': 5,  # Limit for testing
        'db_path': 'test_crawler.db',
        'user_agent': 'Test-Crawler/1.0',
        'analyze_backlinks': True
    }

    # Test URLs
    test_urls = [
        "https://example.com"
    ]

    print(f"Configuration: {config}")
    print(f"Test URLs: {test_urls}")
    print("-" * 40)

    try:
        # Initialize crawler
        print("🚀 Initializing crawler...")
        crawler = EnhancedProductionCrawler(config)
        print("✅ Crawler initialized successfully")

        # Run crawl
        print("📄 Starting test crawl...")
        results = crawler.comprehensive_crawl(test_urls)

        # Print results
        if results.get('success'):
            print("✅ Test crawl completed successfully!")
            crawler.print_summary(results)

            # Show sample backlinks if available
            backlinks = crawler.get_all_backlinks()
            if backlinks:
                print(f"\n🔗 Found {len(backlinks)} backlinks:")
                for i, bl in enumerate(backlinks[:3]):  # Show first 3
                    print(f"  {i+1}. {bl.get('source_url', '')[:50]}... -> {bl.get('target_url', '')[:50]}...")

        else:
            print(f"❌ Test crawl failed: {results.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crawler()
