#!/usr/bin/env python3
"""
Simple Batch Crawler Script for RatCrawler
Runs the existing crawler in batches of 50 URLs at a time
"""

import asyncio
import sys
import os
import time
from datetime import datetime
from typing import List, Optional

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rat.sqlalchemy_database import SQLAlchemyDatabase
from rat.logger import log_manager


class SimpleBatchCrawler:
    """Simple batch processor that uses existing crawler infrastructure"""

    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.db = SQLAlchemyDatabase()

    def get_total_urls_count(self) -> int:
        """Get total count of unique URLs from backlinks"""
        try:
            with self.db.get_session("backlink") as session:
                from sqlalchemy import text

                # Count unique URLs from both source and target columns
                count_query = text("""
                    SELECT COUNT(DISTINCT url) FROM (
                        SELECT source_url as url FROM backlinks WHERE source_url IS NOT NULL
                        UNION
                        SELECT target_url as url FROM backlinks WHERE target_url IS NOT NULL
                    ) unique_urls
                """)

                result = session.execute(count_query).scalar()
                return result or 0

        except Exception as e:
            print(f"❌ Error counting URLs: {e}")
            return 0

    def get_urls_batch(self, page: int, limit: int = 50) -> List[str]:
        """Get a batch of unique URLs using pagination"""
        try:
            offset = (page - 1) * limit

            with self.db.get_session("backlink") as session:
                from sqlalchemy import text

                # Get unique URLs with pagination
                batch_query = text("""
                    SELECT DISTINCT url FROM (
                        SELECT source_url as url FROM backlinks WHERE source_url IS NOT NULL
                        UNION
                        SELECT target_url as url FROM backlinks WHERE target_url IS NOT NULL
                    ) unique_urls
                    ORDER BY url
                    LIMIT :limit OFFSET :offset
                """)

                result = session.execute(batch_query, {"limit": limit, "offset": offset})
                urls = [row[0] for row in result.fetchall()]

                # Basic URL validation
                valid_urls = []
                for url in urls:
                    if url and (url.startswith('http://') or url.startswith('https://')):
                        valid_urls.append(url)

                print(f"📦 Page {page}: Found {len(valid_urls)} valid URLs")
                return valid_urls

        except Exception as e:
            print(f"❌ Error fetching URL batch {page}: {e}")
            return []

    async def run_batch_crawl(self, start_page: int = 1, max_pages: Optional[int] = None):
        """Run the existing crawler in batches"""
        print("🔥 Starting Simple Batch Crawler for RatCrawler")
        print("=" * 60)

        # Get total URL count
        print("🔍 Analyzing database...")
        total_urls = self.get_total_urls_count()

        if total_urls == 0:
            print("❌ No URLs found in backlinks database")
            return

        total_pages = (total_urls + self.batch_size - 1) // self.batch_size

        if max_pages:
            total_pages = min(total_pages, max_pages)

        print(f"📊 Database Analysis:")
        print(f"   Total URLs: {total_urls:,}")
        print(f"   Batch size: {self.batch_size}")
        print(f"   Total pages: {total_pages}")
        print(f"   Starting from page: {start_page}")
        if max_pages:
            print(f"   Processing max pages: {max_pages}")
        print()

        # Import crawler after initial setup
        try:
            from rat.crawler import ProfessionalBacklinkCrawler
        except ImportError:
            print("❌ Could not import crawler. Using alternative approach...")
            return await self.run_simple_batch_process(start_page, total_pages)

        # Process each page
        start_time = time.time()
        total_successful = 0
        total_failed = 0

        for page in range(start_page, start_page + total_pages):
            print(f"\n🚀 Processing Page {page}/{start_page + total_pages - 1}")
            print("-" * 40)

            # Get batch of URLs
            batch_urls = self.get_urls_batch(page, self.batch_size)

            if not batch_urls:
                print(f"📝 No URLs found on page {page}, ending crawl")
                break

            # Create a temporary crawler for this batch
            try:
                crawler = ProfessionalBacklinkCrawler(
                    db_handler=self.db,
                    max_concurrent=5,  # Conservative
                    delay=1.0
                )

                # Create a mini session for this batch
                config_data = {
                    'crawler_type': 'batch_simple',
                    'batch_size': len(batch_urls),
                    'page': page,
                    'timestamp': datetime.now().isoformat()
                }

                session_id, db_name = self.db.create_crawl_session(batch_urls[:10], config_data)
                print(f"✅ Created session {session_id} in {db_name}")

                # Crawl this batch
                batch_start = time.time()
                results = await crawler.crawl_urls_batch(batch_urls, session_id, db_name)
                batch_time = time.time() - batch_start

                # Update totals
                successful = results.get('successful', 0)
                failed = results.get('failed', 0)
                total_successful += successful
                total_failed += failed

                # Progress update
                processed_urls = (page - start_page + 1) * self.batch_size
                elapsed_time = time.time() - start_time
                avg_speed = processed_urls / elapsed_time if elapsed_time > 0 else 0

                print(f"✅ Page {page} completed:")
                print(f"   URLs: {len(batch_urls)}")
                print(f"   Successful: {successful}")
                print(f"   Failed: {failed}")
                print(f"   Time: {batch_time:.1f}s")
                print(f"   Progress: {processed_urls}/{total_urls} ({processed_urls/total_urls*100:.1f}%)")
                print(f"   Average Speed: {avg_speed:.1f} URLs/sec")

                # Finish this session
                self.db.finish_crawl_session(str(session_id), 'completed')

                # Pause between batches
                if page < start_page + total_pages - 1:
                    print("⏸️  Pausing 2 seconds between batches...")
                    await asyncio.sleep(2.0)

            except Exception as e:
                print(f"❌ Error processing page {page}: {e}")
                total_failed += len(batch_urls)

        # Final summary
        total_time = time.time() - start_time
        final_speed = (total_successful + total_failed) / total_time if total_time > 0 else 0

        print("\n🎉 Batch Crawl Completed!")
        print("=" * 60)
        print(f"📊 Final Results:")
        print(f"   Total URLs Processed: {total_successful + total_failed:,}")
        print(f"   Successful Crawls: {total_successful:,}")
        print(f"   Failed Crawls: {total_failed:,}")
        print(f"   Success Rate: {total_successful/(total_successful + total_failed)*100:.1f}%")
        print(f"   Total Time: {total_time/60:.1f} minutes")
        print(f"   Average Speed: {final_speed:.1f} URLs/second")
        print(f"   Pages Processed: {page - start_page + 1}")

    async def run_simple_batch_process(self, start_page: int, total_pages: int):
        """Fallback simple batch processing"""
        print("🔄 Running simple batch URL collection...")

        all_urls = []
        for page in range(start_page, start_page + total_pages):
            batch_urls = self.get_urls_batch(page, self.batch_size)
            if not batch_urls:
                break
            all_urls.extend(batch_urls)

            print(f"📦 Collected page {page}: {len(batch_urls)} URLs (Total: {len(all_urls)})")

            if len(batch_urls) < self.batch_size:  # Last page
                break

        print(f"\n✅ Collection complete: {len(all_urls)} URLs ready for crawling")
        print("💡 You can now use these URLs with your preferred crawler")

        # Save URLs to file for manual processing
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_urls_{timestamp}.txt"

        with open(filename, 'w') as f:
            for url in all_urls:
                f.write(f"{url}\n")

        print(f"💾 URLs saved to: {filename}")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Simple Batch Crawler for RatCrawler')
    parser.add_argument('--start-page', type=int, default=1, help='Page to start from (default: 1)')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to process (default: all)')
    parser.add_argument('--batch-size', type=int, default=50, help='URLs per batch (default: 50)')

    args = parser.parse_args()

    # Create and run batch crawler
    crawler = SimpleBatchCrawler(batch_size=args.batch_size)
    await crawler.run_batch_crawl(
        start_page=args.start_page,
        max_pages=args.max_pages
    )


if __name__ == "__main__":
    asyncio.run(main())
