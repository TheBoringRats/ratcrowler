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
from rat.crawler import EnhancedProductionCrawler

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

def add_necessary_domains_to_seeds(crawler, threshold_score=50):
    """Add domains with high authority scores to seed URLs."""
    try:
        # Get domain authority scores from the database
        domain_scores = crawler.database.get_domain_authority_scores()

        if not domain_scores:
            print("ℹ️ No domain authority scores found")
            return

        # Load current seed URLs
        seed_file = 'seed_urls.json'
        current_seeds = load_seed_urls(seed_file)

        # Extract domains from current seeds
        from urllib.parse import urlparse
        current_domains = {urlparse(url).netloc for url in current_seeds}

        # Find domains that meet the threshold and aren't already in seeds
        new_domains = []
        for domain, score in domain_scores.items():
            if score >= threshold_score and domain not in current_domains:
                # Create a sample URL for the domain
                sample_url = f"https://{domain}"
                new_domains.append(sample_url)
                print(f"📈 Adding high-authority domain to seeds: {domain} (score: {score:.1f})")

        if new_domains:
            # Add new domains to seed file
            updated_seeds = current_seeds + new_domains
            with open(seed_file, 'w') as f:
                json.dump(updated_seeds, f, indent=2)
            print(f"✅ Added {len(new_domains)} new domains to {seed_file}")
            return new_domains
        else:
            print("ℹ️ No new domains meet the threshold for addition to seeds")

    except Exception as e:
        print(f"❌ Error adding domains to seeds: {e}")

    return []

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

    def perform_backlink_extraction():
        """Day 1: Extract backlinks from all seed URLs and store in database."""
        print(f"\n🔗 Starting backlink extraction at {datetime.now()}")
        try:
            # Configure for backlink-focused crawling
            backlink_config = config.copy()
            backlink_config['max_depth'] = 1  # Shallow crawl for backlinks
            backlink_config['max_pages'] = 50  # Limit pages per domain
            backlink_config['analyze_backlinks'] = True

            # Create new crawler instance with backlink config
            backlink_crawler = EnhancedProductionCrawler(backlink_config)

            results = backlink_crawler.comprehensive_crawl(valid_urls)

            if results.get('success'):
                backlink_crawler.print_summary(results)

                # Add high-authority domains to seeds
                new_domains = add_necessary_domains_to_seeds(backlink_crawler)

                print(f"\n✅ Backlink extraction completed successfully!")
                if new_domains:
                    print(f"📈 Added {len(new_domains)} new domains to seed URLs")
            else:
                print(f"\n❌ Backlink extraction failed: {results.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Error during backlink extraction: {e}")

    def perform_seed_domain_crawl():
        """Day 2: Crawl all pages from seed URL domains."""
        print(f"\n🌐 Starting seed domain crawl at {datetime.now()}")
        try:
            # Reload seed URLs (may have been updated)
            current_seeds = load_seed_urls(seed_file)

            # Configure for deeper domain crawling
            domain_config = config.copy()
            domain_config['max_depth'] = 4  # Deeper crawl within domains
            domain_config['max_pages'] = 200  # More pages per domain
            domain_config['stay_on_domain'] = True  # Stay within seed domains
            domain_config['analyze_backlinks'] = False  # Skip backlink analysis

            domain_crawler = EnhancedProductionCrawler(domain_config)
            results = domain_crawler.comprehensive_crawl(current_seeds)

            if results.get('success'):
                domain_crawler.print_summary(results)
                print(f"\n✅ Seed domain crawl completed successfully!")
            else:
                print(f"\n❌ Seed domain crawl failed: {results.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Error during seed domain crawl: {e}")

    def perform_subdomain_crawl():
        """Days 3-4: Crawl necessary subdomain pages."""
        print(f"\n🏗️ Starting subdomain crawl at {datetime.now()}")
        try:
            # Get subdomains from previously crawled data
            subdomains = crawler.database.get_discovered_subdomains()

            if not subdomains:
                print("ℹ️ No subdomains found for crawling")
                return

            # Configure for subdomain crawling
            subdomain_config = config.copy()
            subdomain_config['max_depth'] = 3
            subdomain_config['max_pages'] = 150
            subdomain_config['stay_on_domain'] = False  # Allow subdomain crawling
            subdomain_config['analyze_backlinks'] = True

            subdomain_crawler = EnhancedProductionCrawler(subdomain_config)
            results = subdomain_crawler.comprehensive_crawl(subdomains)

            if results.get('success'):
                subdomain_crawler.print_summary(results)
                print(f"\n✅ Subdomain crawl completed successfully!")
            else:
                print(f"\n❌ Subdomain crawl failed: {results.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Error during subdomain crawl: {e}")

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

    def run_daily_engine_services():
        """Daily 2-hour process: Run all engine services from 12AM-2AM."""
        print(f"\n🚀 Starting daily engine services at {datetime.now()}")

        start_time = time.time()
        max_duration = 2 * 60 * 60  # 2 hours in seconds

        try:
            while time.time() - start_time < max_duration:
                # Run various engine services
                print("🔄 Running engine service cycle...")

                # Service 1: Update domain authority scores
                try:
                    domain_scores = crawler.database.get_domain_authority_scores()
                    if domain_scores:
                        print(f"📊 Updated domain authority for {len(domain_scores)} domains")
                except Exception as e:
                    print(f"⚠️ Domain authority update failed: {e}")

                # Service 2: Recalculate PageRank scores
                try:
                    pagerank_data = crawler.database.get_pagerank_scores()
                    if pagerank_data:
                        print(f"🔢 Recalculated PageRank for {len(pagerank_data)} pages")
                except Exception as e:
                    print(f"⚠️ PageRank calculation failed: {e}")

                # Service 3: Clean up old data
                try:
                    cleanup_count = crawler.database.cleanup_old_data(days_old=30)
                    if cleanup_count > 0:
                        print(f"🧹 Cleaned up {cleanup_count} old records")
                except Exception as e:
                    print(f"⚠️ Data cleanup failed: {e}")

                # Service 4: Update backlink analysis
                try:
                    recent_backlinks = crawler.database.get_recent_backlinks(hours=24)
                    if recent_backlinks:
                        print(f"🔗 Analyzed {len(recent_backlinks)} recent backlinks")
                except Exception as e:
                    print(f"⚠️ Backlink analysis failed: {e}")

                # Wait before next cycle
                time.sleep(300)  # 5 minutes between cycles

        except KeyboardInterrupt:
            print("🛑 Daily engine services interrupted by user")
        except Exception as e:
            print(f"❌ Error in daily engine services: {e}")

        print(f"✅ Daily engine services completed at {datetime.now()}")

    # Set up weekly schedule (Monday to Sunday cycle)
    print("\n⏰ Setting up weekly schedule...")
    schedule.every().monday.at("08:00").do(perform_backlink_extraction)    # Day 1: Backlink extraction
    schedule.every().tuesday.at("08:00").do(perform_seed_domain_crawl)     # Day 2: Seed domain crawl
    schedule.every().wednesday.at("08:00").do(perform_subdomain_crawl)     # Day 3: Subdomain crawl
    schedule.every().thursday.at("08:00").do(perform_subdomain_crawl)      # Day 4: Subdomain crawl (continued)
    schedule.every().friday.at("08:00").do(retrieve_backlinks)             # Day 5: Backlink retrieval
    schedule.every().saturday.at("08:00").do(retrieve_backlinks)           # Day 6: Backlink retrieval
    schedule.every().sunday.at("08:00").do(show_system_status)             # Day 7: System status

    # Set up daily 2-hour engine services (12AM-2AM)
    schedule.every().day.at("00:00").do(run_daily_engine_services)

    print("✅ Weekly schedule configured:")
    print("  - Monday 08:00: Backlink extraction from seed URLs")
    print("  - Tuesday 08:00: Crawl all seed domain pages")
    print("  - Wednesday 08:00: Crawl necessary subdomains")
    print("  - Thursday 08:00: Continue subdomain crawling")
    print("  - Friday 08:00: Backlink data retrieval")
    print("  - Saturday 08:00: Backlink data retrieval")
    print("  - Sunday 08:00: System status report")
    print("  - Daily 00:00-02:00: Engine services (2 hours)")
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
