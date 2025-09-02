#!/usr/bin/env python3
"""
Batch Progress Tracker for RatCrawler
Automatically saves and resumes batch crawling progress
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional


class BatchProgressTracker:
    """Tracks batch crawling progress and saves state to file"""

    def __init__(self, progress_file: str = "batch_progress.json"):
        self.progress_file = progress_file
        self.current_page = 1
        self.batch_size = 50
        self.total_urls_processed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.start_time = None
        self.last_update = None

        # Load existing progress
        self.load_progress()

    def load_progress(self) -> bool:
        """Load progress from file if exists"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)

                self.current_page = data.get('current_page', 1)
                self.batch_size = data.get('batch_size', 50)
                self.total_urls_processed = data.get('total_urls_processed', 0)
                self.total_successful = data.get('total_successful', 0)
                self.total_failed = data.get('total_failed', 0)
                self.start_time = data.get('start_time')
                self.last_update = data.get('last_update')

                print(f"📂 Loaded progress: Resuming from page {self.current_page}")
                print(f"   Total processed: {self.total_urls_processed}")
                print(f"   Successful: {self.total_successful}")
                print(f"   Failed: {self.total_failed}")
                if self.last_update:
                    print(f"   Last update: {self.last_update}")
                print()
                return True
            else:
                print("📂 No previous progress found, starting fresh")
                return False

        except Exception as e:
            print(f"⚠️ Error loading progress: {e}")
            print("📂 Starting fresh")
            return False

    def save_progress(self):
        """Save current progress to file"""
        try:
            data = {
                'current_page': self.current_page,
                'batch_size': self.batch_size,
                'total_urls_processed': self.total_urls_processed,
                'total_successful': self.total_successful,
                'total_failed': self.total_failed,
                'start_time': self.start_time,
                'last_update': datetime.now().isoformat()
            }

            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"💾 Progress saved: Page {self.current_page}")

        except Exception as e:
            print(f"⚠️ Error saving progress: {e}")

    def update_progress(self, successful: int, failed: int):
        """Update progress statistics"""
        self.total_urls_processed += (successful + failed)
        self.total_successful += successful
        self.total_failed += failed

        if self.start_time is None:
            self.start_time = datetime.now().isoformat()

        self.save_progress()

    def next_page(self):
        """Move to next page"""
        self.current_page += 1
        self.save_progress()

    def reset_progress(self):
        """Reset progress to start from beginning"""
        self.current_page = 1
        self.total_urls_processed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.start_time = None
        self.last_update = None

        # Remove progress file
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
            print("🗑️ Progress reset - starting from page 1")

    def get_stats(self) -> Dict:
        """Get current statistics"""
        return {
            'current_page': self.current_page,
            'batch_size': self.batch_size,
            'total_urls_processed': self.total_urls_processed,
            'total_successful': self.total_successful,
            'total_failed': self.total_failed,
            'success_rate': (self.total_successful / self.total_urls_processed * 100) if self.total_urls_processed > 0 else 0,
            'start_time': self.start_time,
            'last_update': self.last_update
        }

    def print_stats(self):
        """Print current statistics"""
        stats = self.get_stats()
        print("📊 Current Progress Stats:")
        print(f"   Current Page: {stats['current_page']}")
        print(f"   Batch Size: {stats['batch_size']}")
        print(f"   URLs Processed: {stats['total_urls_processed']:,}")
        print(f"   Successful: {stats['total_successful']:,}")
        print(f"   Failed: {stats['total_failed']:,}")
        if stats['total_urls_processed'] > 0:
            print(f"   Success Rate: {stats['success_rate']:.1f}%")
        if stats['start_time']:
            print(f"   Started: {stats['start_time']}")
        if stats['last_update']:
            print(f"   Last Update: {stats['last_update']}")
