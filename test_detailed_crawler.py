#!/usr/bin/env python3
"""
Detailed Crawler Test - Shows every parsing step in detail
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rat.auto_batch_crawler import AutoBatchCrawler
from rat.crawler import ProfessionalBacklinkCrawler

async def test_detailed_crawl():
    """Test crawler with maximum detail logging"""
    print("🔍 RatCrawler - Detailed Test Mode")
    print("=" * 50)

    try:
        # Create crawler with detailed logging
        crawler = AutoBatchCrawler(batch_size=2)  # Only 2 URLs for detailed testing

        # Get sample URLs
        sample_urls = crawler.get_backlink_urls_batch(1, 2)
        if not sample_urls:
            print("❌ No URLs found in database")
            return False

        print(f"🎯 Testing with {len(sample_urls)} URLs:")
        for i, url in enumerate(sample_urls, 1):
            print(f"   {i}. {url}")
        print()

        # Initialize detailed crawler
        detailed_crawler = ProfessionalBacklinkCrawler(
            db_handler=crawler.db,
            max_concurrent=1,  # One at a time for detailed logging
            delay=0.5  # Faster for testing
        )

        # Create test session
        config_data = {
            'crawler_type': 'detailed_test',
            'batch_size': len(sample_urls),
            'test_mode': True,
            'timestamp': '2025-09-02T09:00:00'
        }

        session_id, db_name = crawler.db.create_crawl_session(sample_urls, config_data)
        print(f"✅ Test session {session_id} created in {db_name}")
        print()

        # Crawl with maximum detail
        results = await detailed_crawler.crawl_urls_batch(sample_urls, session_id, db_name)

        # Show detailed results
        print("\n" + "="*60)
        print("📊 DETAILED CRAWL RESULTS")
        print("="*60)

        for i, result in enumerate(results['results'], 1):
            print(f"\n🌐 URL {i}: {result.url}")
            print("-" * 40)

            if result.crawl_success:
                print(f"✅ Status: SUCCESS")
                print(f"📄 Title: {result.title}")
                print(f"📝 Description: {result.meta_description[:100] if result.meta_description else 'None'}...")
                print(f"🔢 HTTP Status: {result.http_status_code}")
                print(f"⏱️ Response Time: {result.response_time_ms}ms")
                print(f"📏 Page Size: {result.page_size:,} bytes")
                print(f"🔤 Word Count: {result.word_count:,}" if result.word_count else "🔤 Word Count: N/A")
                print(f"📂 Content Type: {result.content_type}")
                print(f"🌍 Language: {result.language or 'N/A'}")
                print(f"🔗 Internal Links: {result.internal_links_count or 'N/A'}")
                print(f"🔗 External Links: {result.external_links_count or 'N/A'}")
                print(f"🖼️ Images: {result.images_count or 'N/A'}")
                print(f"🔑 Content Hash: {result.content_hash}")

                if result.h1_tags:
                    print(f"🏷️ H1 Tags: {len(result.h1_tags)}")
                    for h1 in result.h1_tags[:3]:
                        print(f"   • {h1[:60]}...")

                if result.h2_tags:
                    print(f"🏷️ H2 Tags: {len(result.h2_tags)}")
                    for h2 in result.h2_tags[:3]:
                        print(f"   • {h2[:60]}...")

                if result.meta_keywords:
                    print(f"🔍 Keywords: {', '.join(result.meta_keywords[:5])}")

                if result.redirect_chain:
                    print(f"🔄 Redirect Chain: {len(result.redirect_chain)} steps")
                    for step in result.redirect_chain:
                        print(f"   → {step}")

                # Show content preview
                if result.content_text:
                    preview = result.content_text[:200].replace('\n', ' ').strip()
                    print(f"📖 Content Preview: {preview}...")

            else:
                print(f"❌ Status: FAILED")
                print(f"💥 Error: {result.error_message}")

        print(f"\n🎉 Test Summary:")
        print(f"   Total URLs: {results['total_urls']}")
        print(f"   Successful: {results['successful']}")
        print(f"   Failed: {results['failed']}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Starting detailed crawler test...")
    success = asyncio.run(test_detailed_crawl())

    if success:
        print("\n✅ Detailed test completed!")
        print("💡 This shows exactly what data is extracted and stored")
    else:
        print("\n❌ Test failed!")
