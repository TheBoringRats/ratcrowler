#!/usr/bin/env python3
"""
Batch Crawl Script for RatCrawler
Simple script to crawl URLs from backlinks database in batches of 50
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rat.sqlalchemy_database import SQLAlchemyDatabase
from rat.crawler import ProfessionalBacklinkCrawler
from rat.logger import log_manager


def get_total_backlink_urls_count(db: SQLAlchemyDatabase) -> int:
    """Get total count of unique URLs from backlinks"""
    try:
        with db.get_session("backlink") as session:
            from sqlalchemy import text

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


def get_backlink_urls_batch(db: SQLAlchemyDatabase, page: int, limit: int = 50) -> list:
    """Get a batch of URLs from backlinks database"""
    try:
        offset = (page - 1) * limit

        with db.get_session("backlink") as session:
            from sqlalchemy import text

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
            valid_urls = [url for url in urls if url and (url.startswith('http://') or url.startswith('https://'))]
            return valid_urls

    except Exception as e:
        print(f"❌ Error fetching URL batch {page}: {e}")
        return []


from typing import Optional

async def run_batch_crawl(start_page: int = 1, max_pages: Optional[int] = None, batch_size: int = 50):
    """Run batch crawling from backlinks database"""
    print("🔥 RatCrawler Batch Mode")
    print("=" * 50)

    # Initialize database
    db = SQLAlchemyDatabase()

    # Get total URL count
    print("🔍 Analyzing backlinks database...")
    total_urls = get_total_backlink_urls_count(db)

    if total_urls == 0:
        print("❌ No URLs found in backlinks database!")
        print("💡 Run the backlink discovery first to populate the database")
        return

    total_pages = (total_urls + batch_size - 1) // batch_size
    if max_pages:
        total_pages = min(total_pages, max_pages)

    print(f"📊 Batch Crawl Setup:")
    print(f"   Total URLs available: {total_urls:,}")
    print(f"   URLs per batch: {batch_size}")
    print(f"   Total pages: {total_pages}")
    print(f"   Starting from page: {start_page}")
    if max_pages:
        print(f"   Processing max pages: {max_pages}")
    print()

    # Initialize crawler
    crawler = ProfessionalBacklinkCrawler(
        db_handler=db,
        max_concurrent=5,  # Conservative for batch processing
        delay=1.5  # Respectful delay
    )

    start_time = time.time()
    total_successful = 0
    total_failed = 0

    try:
        # Process each page
        for page in range(start_page, start_page + total_pages):
            print(f"\n🚀 Processing Page {page}")
            print("-" * 30)

            # Get batch URLs
            batch_urls = get_backlink_urls_batch(db, page, batch_size)

            if not batch_urls:
                print(f"📝 No URLs found on page {page}, ending crawl")
                break

            print(f"📦 Batch size: {len(batch_urls)} URLs")

            # Create a session for this batch
            config_data = {
                'crawler_type': 'batch_crawl',
                'batch_size': len(batch_urls),
                'page': page,
                'timestamp': datetime.now().isoformat()
            }

            try:
                # Use first few URLs as seeds for session creation
                session_seeds = batch_urls[:min(5, len(batch_urls))]
                session_id, db_name = db.create_crawl_session(session_seeds, config_data)
                print(f"✅ Session {session_id} created in {db_name}")

                # Log crawl start
                log_manager.crawler_logger.log_crawl_start(f"batch-{page}", batch_urls, config_data)

                # Crawl this batch
                batch_start = time.time()
                results = await crawler.crawl_urls_batch(batch_urls, session_id, db_name)
                batch_time = time.time() - batch_start

                # Update totals
                successful = results.get('successful', 0)
                failed = results.get('failed', 0)
                total_successful += successful
                total_failed += failed

                # Progress report
                processed_urls = (page - start_page + 1) * batch_size
                elapsed_time = time.time() - start_time
                avg_speed = processed_urls / elapsed_time if elapsed_time > 0 else 0
                eta = (total_pages - (page - start_page + 1)) * (batch_time / 60) if batch_time > 0 else 0

                print(f"✅ Batch {page} completed:")
                print(f"   Successful: {successful}")
                print(f"   Failed: {failed}")
                print(f"   Batch time: {batch_time:.1f}s")
                print(f"   Progress: {processed_urls}/{total_urls} ({processed_urls/total_urls*100:.1f}%)")
                print(f"   Speed: {avg_speed:.1f} URLs/sec")
                print(f"   ETA: {eta:.1f} minutes")

                # Finish this session
                db.finish_crawl_session(str(session_id), 'completed')

                # Pause between batches
                if page < start_page + total_pages - 1:
                    print("⏸️  Pausing 3 seconds...")
                    await asyncio.sleep(3.0)

            except Exception as e:
                print(f"❌ Error processing page {page}: {e}")
                total_failed += len(batch_urls)

        # Final summary
        total_time = time.time() - start_time
        final_speed = (total_successful + total_failed) / total_time if total_time > 0 else 0

        print("\n🎉 Batch Crawl Completed!")
        print("=" * 50)
        print(f"📊 Final Results:")
        print(f"   URLs Available: {total_urls:,}")
        print(f"   URLs Processed: {total_successful + total_failed:,}")
        print(f"   Successful: {total_successful:,}")
        print(f"   Failed: {total_failed:,}")
        if total_successful + total_failed > 0:
            print(f"   Success Rate: {total_successful/(total_successful + total_failed)*100:.1f}%")
        print(f"   Total Time: {total_time/60:.1f} minutes")
        print(f"   Average Speed: {final_speed:.1f} URLs/second")
        print(f"   Pages Processed: {page - start_page + 1}")

    except KeyboardInterrupt:
        print("\n⏹️ Batch crawl interrupted by user")
    except Exception as e:
        print(f"\n❌ Batch crawl failed: {e}")


def main():
    """Main entry point with command line arguments"""
    import argparse

    parser = argparse.ArgumentParser(description='RatCrawler Batch Processing')
    parser.add_argument('--start-page', type=int, default=1,
                       help='Page number to start from (default: 1)')
    parser.add_argument('--max-pages', type=int,
                       help='Maximum number of pages to process (default: all)')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Number of URLs per batch (default: 50)')

    args = parser.parse_args()

    print(f"🕷️ Starting RatCrawler Batch Mode")
    print(f"   Start page: {args.start_page}")
    print(f"   Batch size: {args.batch_size}")
    if args.max_pages:
        print(f"   Max pages: {args.max_pages}")
    print()

    # Run the batch crawl
    asyncio.run(run_batch_crawl(
        start_page=args.start_page,
        max_pages=args.max_pages,
        batch_size=args.batch_size
    ))


if __name__ == "__main__":
    main()
