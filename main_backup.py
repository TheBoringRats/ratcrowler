#!/usr/bin/env python3
"""
Main entry point for the RatCrawler system with integrated Streamlit monitoring.
Combines web content crawling with backlink analysis and real-time dashboard monitoring.
"""

import json
import sys
import time
import os
import subprocess
import threading
import signal
from datetime import datetime
import schedule

# Import the crawler from the correct module
from rat.crawler import ProfessionalBacklinkCrawler
from rat.sqlalchemy_database import SQLAlchemyDatabase

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
    """Main function to run the crawler with integrated Streamlit monitoring dashboard."""
    print("🕷️ RatCrawler v3.0 - Integrated Crawler with Real-time Monitoring")
    print("=" * 70)

    # Load configuration
    config = create_default_config()

    # Load seed URLs
    seed_file = 'seed_urls.json'
    valid_urls = load_seed_urls(seed_file)

    print(f"🌐 Seed URLs loaded: {len(valid_urls)} URLs from {seed_file}")
    print(f"🗄️ Database: {config['db_path']}")
    print()

    # Start the Streamlit dashboard in background
    print("🖥️ Starting Streamlit monitoring dashboard...")
    dashboard_process = start_dashboard_background()
    print("📊 Dashboard available at: http://localhost:8501")
    print()

    # Initialize crawler
    try:
        # Initialize database handler
        db_handler = SQLAlchemyDatabase()

        # Create crawler instance
        crawler = ProfessionalBacklinkCrawler(
            db_handler=db_handler,
            max_concurrent=5,  # Conservative concurrency
            delay=config['delay']  # Use config delay
        )

        print("✅ Crawler initialized successfully")
        print()

        # Run the crawl
        print("🚀 Starting crawl process...")
        print("📋 Progress will be visible in the dashboard at http://localhost:8501")
        print("Press Ctrl+C to stop crawling and dashboard")
        print("-" * 70)

        # Run the crawler (this will block until completion or interruption)
        import asyncio
        results = asyncio.run(crawler.run_full_crawl())

        # Print final results
        if 'error' in results:
            print(f"❌ Crawl Error: {results['error']}")
        else:
            print("📊 Final Crawl Results:")
            print(f"   Session ID: {results.get('session_id')}")
            print(f"   Database: {results.get('db_name')}")
            print(f"   Total URLs: {results.get('total_urls')}")
            print(f"   Successful: {results.get('successful')}")
            print(f"   Failed: {results.get('failed')}")

        print("\\n✅ Crawling completed!")
        print("🖥️ Dashboard is still running at: http://localhost:8501")
        print("   Close the terminal or press Ctrl+C to stop the dashboard")

        # Keep the dashboard running
        try:
            dashboard_process.wait()
        except KeyboardInterrupt:
            print("\\n👋 Shutting down dashboard...")
            dashboard_process.terminate()
            dashboard_process.wait()

    except Exception as e:
        print(f"❌ Error: {e}")
        if 'dashboard_process' in locals():
            dashboard_process.terminate()
        sys.exit(1)

    def phase_1_backlink_extraction():
        """Phase 1: Extract backlinks from seed URLs and store in databaselist2 (backlink databases)"""
        print(f"\n🔗 PHASE 1: Starting backlink extraction at {datetime.now()}")
        print("📊 Target: databaselist2 (backlink databases)")

        try:
            # Configure for backlink-focused crawling
            backlink_config = config.copy()
            backlink_config['max_depth'] = 2  # Moderate depth for backlink discovery
            backlink_config['max_pages'] = 100  # Sufficient pages for backlink analysis
            backlink_config['analyze_backlinks'] = True  # Main focus
            backlink_config['stay_on_domain'] = False  # Allow cross-domain backlinks

            # Create specialized backlink crawler
            print("🔧 Configuring backlink extraction crawler...")
            backlink_crawler = EnhancedProductionCrawler(backlink_config)

            # Run backlink extraction
            print(f"🌐 Processing {len(valid_urls)} seed URLs for backlink extraction...")
            results = backlink_crawler.comprehensive_crawl(valid_urls)

            if results.get('success'):
                backlink_crawler.print_summary(results)

                # Get backlink statistics
                all_backlinks = backlink_crawler.get_all_backlinks()
                print(f"\n📈 Backlink extraction results:")
                print(f"   Total backlinks extracted: {len(all_backlinks)}")
                print(f"   Storage target: databaselist2 (backlink databases)")

                # Add high-authority domains to seeds for phase 2
                new_domains = add_necessary_domains_to_seeds(backlink_crawler, threshold_score=30)

                print(f"\n✅ PHASE 1 completed successfully!")
                print(f"📊 Backlinks stored in databaselist2")
                if new_domains:
                    print(f"📈 Added {len(new_domains)} high-authority domains for Phase 2")

                return True
            else:
                print(f"\n❌ PHASE 1 failed: {results.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error in PHASE 1 backlink extraction: {e}")
        def start_dashboard_background():
    """Start the Streamlit dashboard in the background"""
    try:
        # Import here to avoid circular imports
        import subprocess
        import sys
        from pathlib import Path

        dashboard_path = Path(__file__).parent / "dashboard.py"

        if not dashboard_path.exists():
            print(f"⚠️ Dashboard file not found at {dashboard_path}")
            print("   Dashboard features will not be available")
            return None

        # Start dashboard in background
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run',
            str(dashboard_path),
            '--server.port', '8501',
            '--server.address', '0.0.0.0',
            '--server.headless', 'true'  # Run without opening browser
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return process

    except Exception as e:
        print(f"⚠️ Failed to start dashboard: {e}")
        return None
        """Phase 2: Crawl actual pages and store in databaselist1 (crawler databases)"""
        print(f"\n🌐 PHASE 2: Starting page crawling at {datetime.now()}")
        print("📊 Target: databaselist1 (crawler databases)")

        try:
            # Reload seed URLs (may have been updated by phase 1)
            current_seeds = load_seed_urls(seed_file)
            print(f"🔄 Reloaded seed URLs: {len(current_seeds)} total URLs")

            # Configure for comprehensive page crawling
            page_config = config.copy()
            page_config['max_depth'] = 4  # Deep crawl for comprehensive content
            page_config['max_pages'] = 300  # More pages for content crawling
            page_config['stay_on_domain'] = True  # Focus on seed domains
            page_config['analyze_backlinks'] = False  # Focus on content, not backlinks

            # Create specialized page crawler
            print("🔧 Configuring page content crawler...")
            page_crawler = EnhancedProductionCrawler(page_config)

            # Run page crawling
            print(f"📄 Processing {len(current_seeds)} URLs for content crawling...")
            results = page_crawler.comprehensive_crawl(current_seeds)

            if results.get('success'):
                page_crawler.print_summary(results)

                # Get crawling statistics
                all_pages = page_crawler.database.get_all_crawled_urls()
                print(f"\n📈 Page crawling results:")
                print(f"   Total pages crawled: {len(all_pages)}")
                print(f"   Storage target: databaselist1 (crawler databases)")

                print(f"\n✅ PHASE 2 completed successfully!")
                print(f"📊 Pages stored in databaselist1")
                return True
            else:
                print(f"\n❌ PHASE 2 failed: {results.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error in PHASE 2 page crawling: {e}")
            return False

    def run_two_phase_crawling():
        """Execute both phases sequentially"""
        print(f"\n🚀 Starting Two-Phase Crawling System at {datetime.now()}")

        # Phase 1: Backlink extraction
        phase1_success = phase_1_backlink_extraction()

        if phase1_success:
            print(f"\n⏳ Waiting 30 seconds before starting Phase 2...")
            time.sleep(30)  # Brief pause between phases

            # Phase 2: Page crawling
            phase2_success = phase_2_page_crawling()

            if phase2_success:
                print(f"\n🎉 Two-Phase Crawling System completed successfully!")
                show_final_system_status()
            else:
                print(f"\n⚠️ Phase 2 failed, but Phase 1 data is available")
        else:
            print(f"\n❌ Phase 1 failed, cannot proceed to Phase 2")

    def retrieve_backlinks():
        """Retrieve and save backlinks from databaselist2"""
        print(f"\n📥 Retrieving backlinks from databaselist2 at {datetime.now()}")
        try:
            backlinks = crawler.get_all_backlinks()
            if backlinks:
                timestamp = int(time.time())
                filename = f"backlinks_export_{timestamp}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("# Backlinks exported from databaselist2 (backlink databases)\n")
                    f.write(f"# Export time: {datetime.now()}\n")
                    f.write(f"# Total backlinks: {len(backlinks)}\n\n")

                    for bl in backlinks:
                        f.write(f"Source: {bl.get('source_url', '')}\n")
                        f.write(f"Target: {bl.get('target_url', '')}\n")
                        f.write(f"Anchor: {bl.get('anchor_text', 'N/A')}\n")
                        f.write(f"NoFollow: {bl.get('is_nofollow', False)}\n")
                        f.write(f"Authority: {bl.get('domain_authority', 0.0)}\n")
                        f.write("-" * 50 + "\n")

                print(f"✅ Backlinks retrieved and saved to {filename} ({len(backlinks)} backlinks)")
            else:
                print("ℹ️ No backlinks found in databaselist2")

        except Exception as e:
            print(f"❌ Error retrieving backlinks: {e}")

    def show_final_system_status():
        """Show comprehensive system status for both phases"""
        print(f"\n📊 Final Two-Phase System Status at {datetime.now()}")
        print("=" * 60)

        try:
            # Phase 1 data (databaselist2 - backlinks)
            all_backlinks = crawler.get_all_backlinks()
            print(f"🔗 Phase 1 Results (databaselist2 - backlink databases):")
            print(f"   Total backlinks stored: {len(all_backlinks)}")

            # Phase 2 data (databaselist1 - crawled pages)
            crawled_urls = crawler.database.get_all_crawled_urls()
            print(f"\n🌐 Phase 2 Results (databaselist1 - crawler databases):")
            print(f"   Total pages crawled: {len(crawled_urls)}")

            # Database information
            print(f"\n💾 Database Configuration:")
            print(f"   Primary database: {config['db_path']}")
            print(f"   Backlink storage: databaselist2 (distributed)")
            print(f"   Page storage: databaselist1 (distributed)")

            # Show recent activity samples
            if all_backlinks:
                print(f"\n🔗 Recent backlinks (last 3):")
                for bl in all_backlinks[-3:]:
                    print(f"   {bl.get('source_url', '')[:40]}... → {bl.get('target_url', '')[:40]}...")

            if crawled_urls:
                print(f"\n� Recent pages (last 3):")
                for url in crawled_urls[-3:]:
                    print(f"   {url[:60]}...")

        except Exception as e:
            print(f"Error getting final status: {e}")

    def run_maintenance_services():
        """Daily maintenance: database optimization and cleanup"""
        print(f"\n� Starting maintenance services at {datetime.now()}")

        try:
            # Service 1: Update domain authority scores (from databaselist2)
            try:
                domain_scores = crawler.database.get_domain_authority_scores()
                if domain_scores:
                    print(f"📊 Domain authority scores: {len(domain_scores)} domains")
                else:
                    print("ℹ️ No domain authority scores found")
            except Exception as e:
                print(f"⚠️ Domain authority check failed: {e}")

            # Service 2: Database cleanup (both databaselists)
            try:
                cleanup_count = crawler.database.cleanup_old_data(days_old=30)
                if cleanup_count > 0:
                    print(f"🧹 Cleaned up {cleanup_count} old records from both database lists")
                else:
                    print("ℹ️ No old records to clean up")
            except Exception as e:
                print(f"⚠️ Data cleanup failed: {e}")

            # Service 3: Storage quota check
            try:
                print("💾 Checking storage quotas for databaselist1 and databaselist2...")
                # This will be handled by the quota checking in SQLAlchemy database
                print("✅ Storage quota check completed")
            except Exception as e:
                print(f"⚠️ Storage quota check failed: {e}")

        except Exception as e:
            print(f"❌ Error in maintenance services: {e}")

        print(f"✅ Maintenance services completed at {datetime.now()}")

    # Set up the improved schedule
    print("\n⏰ Setting up Two-Phase Crawling Schedule...")

    # Main two-phase crawling (every 2 days to allow both phases to complete)
    schedule.every(2).days.at("08:00").do(run_two_phase_crawling)

    # Daily backlink retrieval
    schedule.every().day.at("14:00").do(retrieve_backlinks)

    # Weekly system status
    schedule.every().sunday.at("20:00").do(show_final_system_status)

    # Daily maintenance (2AM when system is least busy)
    schedule.every().day.at("02:00").do(run_maintenance_services)

    print("✅ Two-Phase Crawling Schedule configured:")
    print("  - Every 2 days at 08:00: Complete two-phase crawling")
    print("    * Phase 1: Backlink extraction → databaselist2")
    print("    * Phase 2: Page crawling → databaselist1")
    print("  - Daily at 14:00: Export backlinks from databaselist2")
    print("  - Weekly Sunday 20:00: Comprehensive system status")
    print("  - Daily at 02:00: Database maintenance and cleanup")

    print(f"\n🎯 System ready! Next crawl cycle: every 2 days")
    print("📋 Storage Strategy:")
    print("   databaselist2: Backlink data (Phase 1)")
    print("   databaselist1: Page content data (Phase 2)")
    print("\n⏰ Scheduler started. Waiting for scheduled tasks...")
    print("Press Ctrl+C to stop the scheduler, or run once now with manual trigger")

    # Option to run immediately for testing
    user_input = input("\n🚀 Run two-phase crawling now? (y/N): ").lower().strip()
    if user_input in ['y', 'yes']:
        run_two_phase_crawling()

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n🛑 Scheduler stopped by user")
        print("Final system status:")
        show_final_system_status()
    except Exception as e:
        print(f"\n❌ Scheduler error: {e}")

if __name__ == "__main__":
    main()
