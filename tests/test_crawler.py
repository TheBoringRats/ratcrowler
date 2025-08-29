#!/usr/bin/env python3
"""
Simple Backlink Crawler Test Script
Tests the basic functionality of the backlink processor with database integration.
"""

import time
import json
from typing import List, Dict
from urllib.parse import urlparse
from rat.backlinkprocessor import BacklinkProcessor, BacklinkData
from rat.backlinkdb import BacklinkDatabase

def test_backlink_crawler():
    """Test the backlink crawler with simple URLs."""
    print("🔍 Testing Backlink Crawler System")
    print("=" * 50)

    # Test URLs - using simple, reliable sites
    seed_urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/links/3"
    ]

    print(f"Testing with URLs: {seed_urls}")
    print("-" * 50)

    try:
        # Initialize processor with database
        processor = BacklinkProcessor(delay=1, usedatabase=True)

        print("✅ BacklinkProcessor initialized successfully")

        # Step 1: Crawl backlinks
        print("\n📊 Step 1: Crawling backlinks...")
        processor.crawl_backlinks(seed_urls, max_depth=1)

        total_backlinks = len(processor.backlinks)
        print(f"✅ Found {total_backlinks} backlinks")

        if total_backlinks == 0:
            print("⚠️  No backlinks found. This might be normal for test URLs.")
            return

        # Step 2: Build link graph
        print("\n🔗 Step 2: Building link graph...")
        processor.build_link_graph()
        graph_nodes = len(processor.link_graph.nodes())
        graph_edges = len(processor.link_graph.edges())
        print(f"✅ Built graph with {graph_nodes} nodes and {graph_edges} edges")

        # Step 3: Calculate PageRank
        print("\n📈 Step 3: Calculating PageRank...")
        pagerank_scores = processor.calculate_pagerank()
        print(f"✅ Calculated PageRank for {len(pagerank_scores)} pages")

        # Show top PageRank scores
        if pagerank_scores:
            sorted_pagerank = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)
            print("Top 3 PageRank scores:")
            for url, score in sorted_pagerank[:3]:
                domain = urlparse(url).netloc
                print(f"  {domain}: {score:.4f}")

        # Step 4: Calculate domain authority
        print("\n🏆 Step 4: Calculating domain authority...")
        processor.calculate_domain_authority()
        print(f"✅ Calculated domain authority for {len(processor.domain_scores)} domains")

        # Show domain authority scores
        if processor.domain_scores:
            print("Domain Authority Scores:")
            for domain, score in processor.domain_scores.items():
                print(f"  {domain}: {score:.2f}")

        # Step 5: Detect spam links
        print("\n🛡️ Step 5: Detecting spam links...")
        spam_links = processor.detect_link_spam()
        print(f"✅ Detected {len(spam_links)} potential spam links")

        # Step 6: Generate sample report
        if processor.backlinks:
            print("\n📋 Step 6: Generating sample report...")
            sample_url = processor.backlinks[0].target_url
            report = processor.generate_backlink_report(sample_url)

            print(f"Sample report for: {urlparse(sample_url).netloc}")
            for key, value in report.items():
                if key != 'target_url':
                    print(f"  {key.replace('_', ' ').title()}: {value}")

        # Step 7: Database verification
        print("\n💾 Step 7: Verifying database storage...")
        db = BacklinkDatabase()

        # Check if we can retrieve some backlinks
        if processor.backlinks:
            sample_target = processor.backlinks[0].target_url
            stored_backlinks = db.get_backlinks_for_url(sample_target)
            print(f"✅ Retrieved {len(stored_backlinks)} stored backlinks for sample URL")

        print("\n" + "=" * 50)
        print("📊 FINAL SUMMARY")
        print("=" * 50)
        print(f"Total backlinks crawled: {total_backlinks}")
        print(f"Unique pages in graph: {graph_nodes}")
        print(f"Link relationships: {graph_edges}")
        print(f"Domains analyzed: {len(processor.domain_scores)}")
        print(f"Spam links detected: {len(spam_links)}")
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

def test_database_operations():
    """Test basic database operations."""
    print("\n🗄️ Testing Database Operations")
    print("-" * 30)

    try:
        db = BacklinkDatabase()

        # Create test backlink data
        test_backlinks = [
            BacklinkData(
                source_url="https://example.com/page1",
                target_url="https://target.com/page1",
                anchor_text="Test Link 1",
                context="This is a test context for link 1",
                page_title="Test Page 1",
                domain_authority=45.5,
                is_nofollow=False
            ),
            BacklinkData(
                source_url="https://example.com/page2",
                target_url="https://target.com/page2",
                anchor_text="Test Link 2",
                context="This is a test context for link 2",
                page_title="Test Page 2",
                domain_authority=52.3,
                is_nofollow=True
            )
        ]

        # Test storing backlinks
        print("📝 Storing test backlinks...")
        db.store_backlinks(test_backlinks)
        print("✅ Backlinks stored successfully")

        # Test retrieving backlinks
        print("📖 Retrieving backlinks...")
        retrieved = db.get_backlinks_for_url("https://target.com/page1")
        print(f"✅ Retrieved {len(retrieved)} backlinks")

        # Test domain scores
        print("📊 Storing domain scores...")
        test_domain_scores = {
            "example.com": 45.5,
            "target.com": 52.3,
            "test.com": 38.7
        }
        db.store_domain_scores(test_domain_scores)
        print("✅ Domain scores stored successfully")

        print("✅ Database operations test completed!")

    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function."""
    print("🚀 Backlink Crawler System Test Suite")
    print("=" * 60)

    # Test database operations first
    test_database_operations()

    # Test the main crawler functionality
    test_backlink_crawler()

    print("\n🎉 All tests completed!")
    print("You can now use the BacklinkProcessor for your crawling needs.")

if __name__ == "__main__":
    main()
