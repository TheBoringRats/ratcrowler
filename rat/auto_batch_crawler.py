"""
Enhanced Batch Crawler for RatCrawler
Automatically crawls in batches of 50 URLs with progress tracking
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import text

from .sqlalchemy_database import SQLAlchemyDatabase
from .crawler import ProfessionalBacklinkCrawler
from .progress import progress_tracker
from .logger import log_manager


class AutoBatchCrawler:
    """
    Automatic batch crawler that:
    - Crawls 50 URLs at a time from backlinks database
    - Saves progress automatically
    - Resumes from last saved page on restart
    """

    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.db = SQLAlchemyDatabase()
        self.progress_data = progress_tracker.load_progress()

        # Update batch size if different
        if self.progress_data["batch_size"] != batch_size:
            self.progress_data["batch_size"] = batch_size

        print(f"🔄 Auto Batch Crawler initialized (batch size: {batch_size})")

    def get_total_backlink_urls_count(self) -> int:
        """Get total count of unique URLs from backlinks"""
        try:
            with self.db.get_session("backlink") as session:
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

    def get_backlink_urls_batch(self, page: int, limit: int = 50) -> List[str]:
        """Get a batch of URLs from backlinks database"""
        try:
            offset = (page - 1) * limit

            with self.db.get_session("backlink") as session:
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

    def show_startup_info(self):
        """Display startup information and progress"""
        print("🔥 RatCrawler Auto Batch Mode")
        print("=" * 50)

        # Get total URLs
        total_urls = self.get_total_backlink_urls_count()
        self.progress_data["total_urls"] = total_urls

        if total_urls == 0:
            print("❌ No URLs found in backlinks database!")
            print("💡 Run backlink discovery first to populate the database")
            return False

        total_pages = (total_urls + self.batch_size - 1) // self.batch_size
        current_page = self.progress_data["current_page"]

        print(f"📊 Database Status:")
        print(f"   Total URLs: {total_urls:,}")
        print(f"   URLs per batch: {self.batch_size}")
        print(f"   Total pages: {total_pages}")
        print()

        # Show current progress
        progress_tracker.show_progress(self.progress_data)

        if current_page > 1:
            print(f"🔄 Resuming from page {current_page}")
        else:
            print(f"🚀 Starting fresh crawl from page 1")

        print()
        return True

    async def crawl_single_batch(self, page: int, crawler: ProfessionalBacklinkCrawler) -> Dict:
        """Crawl a single batch and return results"""
        print(f"📦 Processing Page {page}")
        print("-" * 30)

        # Get batch URLs
        batch_urls = self.get_backlink_urls_batch(page, self.batch_size)

        if not batch_urls:
            print(f"📝 No URLs found on page {page}")
            return {"urls_processed": 0, "successful": 0, "failed": 0, "finished": True}

        print(f"🔍 Found {len(batch_urls)} URLs in this batch")

        # Create session for this batch
        config_data = {
            'crawler_type': 'auto_batch_crawl',
            'batch_size': len(batch_urls),
            'page': page,
            'auto_mode': True,
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Create session using first few URLs as seeds
            session_seeds = batch_urls[:min(5, len(batch_urls))]
            session_id, db_name = self.db.create_crawl_session(session_seeds, config_data)

            # Update progress with session info
            self.progress_data["session_id"] = session_id
            self.progress_data["db_name"] = db_name

            print(f"✅ Session {session_id} created in {db_name}")

            # Log crawl start
            log_manager.crawler_logger.log_crawl_start(f"auto-batch-{page}", batch_urls, config_data)

            # Crawl this batch
            batch_start = time.time()
            results = await crawler.crawl_urls_batch(batch_urls, session_id, db_name)
            batch_time = time.time() - batch_start

            # Get results
            successful = results.get('successful', 0)
            failed = results.get('failed', 0)

            # Finish session
            self.db.finish_crawl_session(str(session_id), 'completed')

            # Progress report
            total_processed = self.progress_data["urls_processed"] + len(batch_urls)
            completion = (total_processed / self.progress_data["total_urls"]) * 100 if self.progress_data["total_urls"] > 0 else 0

            print(f"✅ Page {page} completed:")
            print(f"   URLs: {len(batch_urls)}")
            print(f"   Successful: {successful}")
            print(f"   Failed: {failed}")
            print(f"   Time: {batch_time:.1f}s")
            print(f"   Overall Progress: {completion:.1f}%")
            print()

            return {
                "urls_processed": len(batch_urls),
                "successful": successful,
                "failed": failed,
                "batch_time": batch_time,
                "finished": False
            }

        except Exception as e:
            print(f"❌ Error processing page {page}: {e}")
            return {
                "urls_processed": len(batch_urls),
                "successful": 0,
                "failed": len(batch_urls),
                "finished": False
            }

    async def run_auto_crawl(self) -> bool:
        """Run automatic batch crawling with progress tracking"""

        # Show startup info
        if not self.show_startup_info():
            return False

        # Mark crawl as started
        progress_tracker.mark_crawl_start(self.progress_data)

        # Initialize crawler
        crawler = ProfessionalBacklinkCrawler(
            db_handler=self.db,
            max_concurrent=5,  # Conservative for batch processing
            delay=1.5  # Respectful delay
        )

        start_time = time.time()
        current_page = self.progress_data["current_page"]

        try:
            while True:
                # Crawl current page
                batch_results = await self.crawl_single_batch(current_page, crawler)

                # Update progress
                progress_tracker.update_page_progress(self.progress_data, current_page, batch_results)

                # Check if we're done
                if batch_results.get("finished", False):
                    print("🎉 All pages processed!")
                    break

                # Move to next page
                current_page += 1

                # Pause between batches
                print("⏸️  Pausing 3 seconds between batches...")
                await asyncio.sleep(3.0)

        except KeyboardInterrupt:
            print("\n⏹️ Crawl interrupted by user")
            print(f"📝 Progress saved. Will resume from page {current_page + 1} next time.")

        except Exception as e:
            print(f"\n❌ Crawl error: {e}")
            print(f"📝 Progress saved. Will resume from page {current_page + 1} next time.")

        finally:
            # Mark crawl as stopped and save final progress
            progress_tracker.mark_crawl_stop(self.progress_data)

            # Final summary
            total_time = time.time() - start_time
            total_processed = self.progress_data["urls_processed"]

            print("\n📊 Session Summary:")
            print("=" * 30)
            print(f"   URLs Processed: {total_processed:,}")
            print(f"   Successful: {self.progress_data['successful_crawls']:,}")
            print(f"   Failed: {self.progress_data['failed_crawls']:,}")
            print(f"   Session Time: {total_time/60:.1f} minutes")
            print(f"   Next Resume Page: {self.progress_data['current_page']}")

            return True


async def run_auto_batch_crawler():
    """Main entry point for automatic batch crawling"""
    crawler = AutoBatchCrawler(batch_size=50)
    return await crawler.run_auto_crawl()
