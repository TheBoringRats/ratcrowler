#!/usr/bin/env python3
"""
Main entry point for the RatCrawler system with scheduled crawling.
Combines web content crawling with backlink analysis using automated scheduling.
"""

import json
import sys
import time
import os
from datetime import datetime
import schedule

# Import the crawler from the correct module
from crawler import EnhancedProductionCrawler

def create_default_config():
    """Create default configuration for the crawler."""
    return {
        'delay': 1.5,
        'max_depth': 3,
        'max_pages': 100,
        'stay_on_domain': True,
        'allowed_domains': [],
        'export_json': False,
        'export_csv': False,
        'db_path': 'website_crawler.db',
        'user_agent': 'Enhanced-Web-Crawler/1.0 (+https://github.com/TheBoringRats/ratcrowler)',
        'recrawl_days': 7,
        'analyze_backlinks': True,  # Enable backlink analysis
    }

def load_seed_urls(seed_file='seed_urls.json'):
    """Load seed URLs from JSON file."""
    try:
        if not os.path.exists(seed_file):
            print(f"❌ Seed file {seed_file} not found!")
            print("Creating default seed_urls.json with sample URLs...")
            default_urls = [
                "https://example.com",
                "https://github.com",
                "https://stackoverflow.com",
                "https://wikipedia.org",
                "https://python.org"
            ]
            with open(seed_file, 'w') as f:
                json.dump(default_urls, f, indent=2)
            print(f"✅ Created {seed_file} with sample URLs")
            return default_urls

        with open(seed_file, 'r') as f:
            seed_urls = json.load(f)

        valid_urls = [url for url in seed_urls if url.startswith(('http://', 'https://'))]
        if not valid_urls:
            raise ValueError("No valid URLs found in seed file")

        return valid_urls

    except Exception as e:
        print(f"❌ Error loading seed file: {e}")
        sys.exit(1)

def main():
    """Main function to run the scheduled crawler."""
    # Load configuration
    config = create_default_config()

    # Load seed URLs
    seed_file = 'seed_urls.json'
    valid_urls = load_seed_urls(seed_file)

    print("🔍 RatCrawler v3.0 - Enhanced Production Crawler")
    print(f"Database: {config['db_path']}")
    print(f"Seed URLs from {seed_file}: {len(valid_urls)} URLs")
    print("-" * 50)

    # Initialize crawler
    try:
        crawler = EnhancedProductionCrawler(config)
        print("✅ Crawler initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize crawler: {e}")
        sys.exit(1)

    def perform_full_crawl():
        """Perform a full comprehensive crawl."""
        print(f"\n🚀 Starting full crawl at {datetime.now()}")
        try:
            results = crawler.comprehensive_crawl(valid_urls)

            if results.get('success'):
                crawler.print_summary(results)
                if config.get('export_json') or config.get('export_csv'):
                    crawler.export_results(results)
                print("\n✅ Full crawl completed successfully!")
            else:
                print(f"\n❌ Full crawl failed: {results.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Error during full crawl: {e}")

    def retrieve_backlinks():
        """Retrieve and save backlinks from database."""
        print(f"\n📥 Retrieving backlinks from database at {datetime.now()}")
        try:
            backlinks = crawler.get_all_backlinks()
            if backlinks:
                timestamp = int(time.time())
                filename = f"backlinks_query_{timestamp}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    for bl in backlinks:
                        f.write(f"Source: {bl.get('source_url', '')}, Target: {bl.get('target_url', '')}, NoFollow: {bl.get('is_nofollow', '')}\n")
                print(f"✅ Backlinks retrieved and saved to {filename} ({len(backlinks)} backlinks)")
            else:
                print("ℹ️ No backlinks found in database")

        except Exception as e:
            print(f"❌ Error retrieving backlinks: {e}")

    def show_system_status():
        """Show current system status."""
        print(f"\n📊 System Status at {datetime.now()}")
        try:
            # Get general database statistics
            all_backlinks = crawler.get_all_backlinks()
            crawled_urls = crawler.database.get_all_crawled_urls()

            print(f"Total pages crawled: {len(crawled_urls)}")
            print(f"Total backlinks in database: {len(all_backlinks)}")
            print(f"Database file: {config['db_path']}")

            # Show recent backlinks if available
            if all_backlinks:
                print("Recent backlinks:")
                for bl in all_backlinks[-3:]:  # Show last 3
                    print(f"  {bl.get('source_url', '')[:50]}... -> {bl.get('target_url', '')[:50]}...")

        except Exception as e:
            print(f"Error getting status: {e}")

    # Set up schedule (one day full crawl, five days query)
    print("\n⏰ Setting up scheduled tasks...")
    schedule.every().monday.at("08:00").do(perform_full_crawl)
    schedule.every().tuesday.at("08:00").do(retrieve_backlinks)
    schedule.every().wednesday.at("08:00").do(retrieve_backlinks)
    schedule.every().thursday.at("08:00").do(retrieve_backlinks)
    schedule.every().friday.at("08:00").do(retrieve_backlinks)
    schedule.every().saturday.at("08:00").do(retrieve_backlinks)
    schedule.every().sunday.at("08:00").do(show_system_status)

    print("✅ Scheduler configured:")
    print("  - Monday 08:00: Full crawl")
    print("  - Tue-Fri 08:00: Backlink retrieval")
    print("  - Sunday 08:00: System status")
    print("\n⏰ Scheduler started. Waiting for scheduled tasks...")
    print("Press Ctrl+C to stop the scheduler")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n🛑 Scheduler stopped by user")
        print("Final system status:")
        show_system_status()
    except Exception as e:
        print(f"\n❌ Scheduler error: {e}")

if __name__ == "__main__":
    main()
