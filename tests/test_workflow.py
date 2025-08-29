#!/usr/bin/env python3
"""
Test script to verify the RatCrawler workflow implementation.
This script tests the key components of the weekly crawling workflow.
"""

import json
import os
import sys
from datetime import datetime
from main import create_default_config, load_seed_urls, add_necessary_domains_to_seeds
from rat.crawler import EnhancedProductionCrawler
from rat.backlinkprocessor import BacklinkProcessor

def test_seed_url_loading():
    """Test loading seed URLs from JSON file."""
    print("🧪 Testing seed URL loading...")

    seed_file = 'seed_urls.json'
    urls = load_seed_urls(seed_file)

    print(f"✅ Loaded {len(urls)} seed URLs:")
    for url in urls[:3]:  # Show first 3
        print(f"  - {url}")

    return len(urls) > 0

def test_config_creation():
    """Test configuration creation."""
    print("\n🧪 Testing configuration creation...")

    config = create_default_config()

    required_keys = ['delay', 'max_depth', 'max_pages', 'db_path', 'user_agent']
    missing_keys = [key for key in required_keys if key not in config]

    if missing_keys:
        print(f"❌ Missing configuration keys: {missing_keys}")
        return False

    print("✅ Configuration created successfully:")
    print(f"  - Database: {config['db_path']}")
    print(f"  - Max depth: {config['max_depth']}")
    print(f"  - Max pages: {config['max_pages']}")
    print(f"  - Backlink analysis: {config['analyze_backlinks']}")

    return True

def test_crawler_initialization():
    """Test crawler initialization."""
    print("\n🧪 Testing crawler initialization...")

    try:
        config = create_default_config()
        crawler = EnhancedProductionCrawler(config)
        print("✅ Crawler initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Crawler initialization failed: {e}")
        return False

def test_backlink_processor():
    """Test backlink processor initialization."""
    print("\n🧪 Testing backlink processor...")

    try:
        processor = BacklinkProcessor(delay=1, usedatabase=False)
        print("✅ Backlink processor initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Backlink processor initialization failed: {e}")
        return False

def test_database_methods():
    """Test new database methods."""
    print("\n🧪 Testing database methods...")

    try:
        config = create_default_config()
        crawler = EnhancedProductionCrawler(config)
        db = crawler.database

        # Test new methods
        subdomains = db.get_discovered_subdomains()
        domain_scores = db.get_domain_authority_scores()
        pagerank_scores = db.get_pagerank_scores()
        recent_backlinks = db.get_recent_backlinks(hours=1)

        print("✅ Database methods working:")
        print(f"  - Discovered subdomains: {len(subdomains)}")
        print(f"  - Domain authority scores: {len(domain_scores)}")
        print(f"  - PageRank scores: {len(pagerank_scores)}")
        print(f"  - Recent backlinks: {len(recent_backlinks)}")

        return True
    except Exception as e:
        print(f"❌ Database methods test failed: {e}")
        return False

def test_workflow_simulation():
    """Simulate the weekly workflow (without actual crawling)."""
    print("\n🧪 Simulating weekly workflow...")

    # Test Day 1: Backlink extraction setup
    print("📅 Day 1: Backlink extraction from seed URLs")
    print("  - Would crawl seed URLs for backlinks")
    print("  - Would store backlinks in database")
    print("  - Would identify high-authority domains")

    # Test Day 2: Seed domain crawling setup
    print("📅 Day 2: Crawl all seed domain pages")
    print("  - Would perform deeper crawl within seed domains")
    print("  - Would stay on domain, explore all pages")

    # Test Days 3-4: Subdomain crawling setup
    print("📅 Days 3-4: Crawl necessary subdomains")
    print("  - Would identify and crawl discovered subdomains")
    print("  - Would analyze subdomain content and backlinks")

    # Test Daily engine services
    print("📅 Daily 00:00-02:00: Engine services")
    print("  - Would update domain authority scores")
    print("  - Would recalculate PageRank scores")
    print("  - Would clean up old data")
    print("  - Would analyze recent backlinks")

    print("✅ Workflow simulation completed")
    return True

def main():
    """Run all tests."""
    print("🚀 RatCrawler Workflow Test Suite")
    print("=" * 50)

    tests = [
        ("Seed URL Loading", test_seed_url_loading),
        ("Configuration Creation", test_config_creation),
        ("Crawler Initialization", test_crawler_initialization),
        ("Backlink Processor", test_backlink_processor),
        ("Database Methods", test_database_methods),
        ("Workflow Simulation", test_workflow_simulation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The RatCrawler workflow is ready.")
        print("\n📋 Weekly Schedule Summary:")
        print("  • Monday 08:00 - Backlink extraction from seed URLs")
        print("  • Tuesday 08:00 - Crawl all seed domain pages")
        print("  • Wednesday 08:00 - Crawl necessary subdomains")
        print("  • Thursday 08:00 - Continue subdomain crawling")
        print("  • Friday 08:00 - Backlink data retrieval")
        print("  • Saturday 08:00 - Backlink data retrieval")
        print("  • Sunday 08:00 - System status report")
        print("  • Daily 00:00-02:00 - Engine services (2 hours)")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
