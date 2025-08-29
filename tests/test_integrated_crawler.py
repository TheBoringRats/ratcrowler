#!/usr/bin/env python3
"""
Test script for the integrated backlink crawler
"""

from rat.integrated_backlink_crawler import IntegratedBacklinkContentCrawler
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_integrated_crawler():
    """Test the integrated backlink crawler"""

    print("=== Testing Integrated Backlink Crawler ===")

    # Initialize the crawler with config
    config = {
        'delay': 1.0,
        'timeout': 10,
        'db_path': 'website_crawler.db'
    }

    crawler = IntegratedBacklinkContentCrawler(config)

    # Test URLs for backlink discovery
    test_urls = [
        "https://httpbin.org/html",
        "https://example.com"
    ]

    print(f"\n1. Starting backlink discovery from {len(test_urls)} seed URLs")

    # Phase 1: Discover backlinks
    phase1_summary = crawler.phase1_discover_backlinks(test_urls)
    print(f"   ✓ Phase 1 complete:")
    print(f"     - Total backlinks found: {phase1_summary['total_backlinks_found']}")
    print(f"     - Unique URLs: {phase1_summary['unique_urls_discovered']}")
    print(f"     - Domains analyzed: {phase1_summary['domains_analyzed']}")
    print(f"     - Discovery time: {phase1_summary['discovery_time_seconds']}s")

    print(f"\n2. Starting content crawling of discovered URLs")

    # Phase 2: Crawl content from discovered backlinks
    phase2_summary = crawler.phase2_crawl_content()
    print(f"   ✓ Phase 2 complete:")
    print(f"     - Pages crawled: {phase2_summary['pages_crawled']}")
    print(f"     - Successful: {phase2_summary['successful_crawls']}")
    print(f"     - Failed: {phase2_summary['failed_crawls']}")

    print(f"\n3. Generating insights")

    # Phase 3: Generate insights
    insights = crawler.phase3_generate_insights(phase1_summary, phase2_summary)
    print(f"   ✓ Analysis complete:")
    print(f"     - Top domains by links: {len(insights.get('top_domains', []))}")
    print(f"     - Content analysis: {len(insights.get('content_insights', {}))}")

    print(f"\n4. Checking database contents")

    # Check databases using proper methods
    import sqlite3

    # Check backlinks database
    backlink_conn = sqlite3.connect('backlinks.db')
    backlink_count = backlink_conn.execute("SELECT COUNT(*) FROM backlinks").fetchone()[0]
    backlink_conn.close()
    print(f"   ✓ Stored {backlink_count} backlinks in database")

    # Check content database
    content_conn = sqlite3.connect('website_crawler.db')
    pages_count = content_conn.execute("SELECT COUNT(*) FROM crawled_pages").fetchone()[0]
    content_conn.close()
    print(f"   ✓ Stored {pages_count} pages in content database")

    print(f"\n=== Test Complete ===")
    print(f"✓ Backlink discovery: {phase1_summary['total_backlinks_found']} backlinks found")
    print(f"✓ Content crawling: {phase2_summary['pages_crawled']} pages processed")
    print(f"✓ Database storage: {backlink_count} backlinks, {pages_count} pages")

if __name__ == "__main__":
    test_integrated_crawler()
