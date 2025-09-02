"""
Progress tracking system for batch crawling
Saves and loads the current page number for resuming crawls
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional


class CrawlProgress:
    """Manages crawl progress tracking and persistence"""

    def __init__(self, progress_file: str = "crawl_progress.json"):
        self.progress_file = progress_file
        self.default_data = {
            "current_page": 1,
            "batch_size": 50,
            "total_urls": 0,
            "urls_processed": 0,
            "successful_crawls": 0,
            "failed_crawls": 0,
            "last_update": None,
            "session_id": None,
            "db_name": None,
            "is_running": False
        }

    def load_progress(self) -> Dict:
        """Load progress from file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)

                # Merge with defaults to handle new fields
                progress = self.default_data.copy()
                progress.update(data)

                # If crawler was running when stopped, mark it as not running
                if progress.get("is_running", False):
                    progress["is_running"] = False
                    self.save_progress(progress)

                return progress
            else:
                return self.default_data.copy()

        except Exception as e:
            print(f"⚠️ Error loading progress: {e}")
            return self.default_data.copy()

    def save_progress(self, progress_data: Dict):
        """Save progress to file"""
        try:
            progress_data["last_update"] = datetime.now().isoformat()

            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)

        except Exception as e:
            print(f"⚠️ Error saving progress: {e}")

    def mark_crawl_start(self, progress_data: Dict):
        """Mark crawl as started"""
        progress_data["is_running"] = True
        self.save_progress(progress_data)

    def mark_crawl_stop(self, progress_data: Dict):
        """Mark crawl as stopped"""
        progress_data["is_running"] = False
        self.save_progress(progress_data)

    def update_page_progress(self, progress_data: Dict, page: int, batch_results: Dict):
        """Update progress after completing a page"""
        progress_data["current_page"] = page + 1  # Next page to process
        progress_data["urls_processed"] += batch_results.get("urls_processed", 0)
        progress_data["successful_crawls"] += batch_results.get("successful", 0)
        progress_data["failed_crawls"] += batch_results.get("failed", 0)

        self.save_progress(progress_data)

    def reset_progress(self):
        """Reset progress to start from beginning"""
        self.save_progress(self.default_data.copy())
        print("🔄 Progress reset to start from page 1")

    def show_progress(self, progress_data: Dict):
        """Display current progress"""
        print(f"📊 Current Progress:")
        print(f"   Current Page: {progress_data['current_page']}")
        print(f"   Batch Size: {progress_data['batch_size']}")
        print(f"   URLs Processed: {progress_data['urls_processed']:,}")
        print(f"   Successful: {progress_data['successful_crawls']:,}")
        print(f"   Failed: {progress_data['failed_crawls']:,}")

        if progress_data['total_urls'] > 0:
            completion = (progress_data['urls_processed'] / progress_data['total_urls']) * 100
            print(f"   Completion: {completion:.1f}%")

        if progress_data['last_update']:
            print(f"   Last Update: {progress_data['last_update']}")

        print()


# Global progress tracker instance
progress_tracker = CrawlProgress()
