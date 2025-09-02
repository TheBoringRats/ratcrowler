#!/usr/bin/env python3
"""
RatCrawler - Automatic Batch Web Crawler
Automatically crawls 50 URLs at a time, saves progress, and resumes from where it left off
"""

import asyncio
import sys
import os
import subprocess
import signal
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rat.auto_batch_crawler import run_auto_batch_crawler
from rat.progress import progress_tracker
from rat.logger import log_manager


def start_dashboard_background():
    """Start the dashboard in background"""
    try:
        dashboard_process = subprocess.Popen([
            sys.executable, "run_enhanced_dashboard.py"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return dashboard_process
    except Exception as e:
        print(f"⚠️ Could not start dashboard: {e}")
        return None


def start_log_api_background():
    """Start the log API in background"""
    try:
        api_process = subprocess.Popen([
            sys.executable, "rat/log_api.py"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return api_process
    except Exception as e:
        print(f"⚠️ Could not start log API: {e}")
        return None


def show_help():
    """Show help information"""
    print("🕷️ RatCrawler - Automatic Batch Web Crawler")
    print("=" * 50)
    print()
    print("Usage: python main.py [command]")
    print()
    print("Commands:")
    print("  (no command)  - Start automatic batch crawling")
    print("  --reset       - Reset progress and start from page 1")
    print("  --status      - Show current crawl progress")
    print("  --help        - Show this help message")
    print()
    print("Features:")
    print("  • Crawls 50 URLs at a time from backlinks database")
    print("  • Automatically saves progress after each batch")
    print("  • Resumes from last saved page on restart")
    print("  • Includes dashboard at http://localhost:8501")
    print("  • Includes log API at http://localhost:8000")
    print()
    print("Progress file: crawl_progress.json")
    print()


def show_status():
    """Show current crawl status"""
    progress_data = progress_tracker.load_progress()

    print("🕷️ RatCrawler Status")
    print("=" * 30)
    progress_tracker.show_progress(progress_data)

    if progress_data["is_running"]:
        print("⚠️ Crawler appears to be running (or was not shut down properly)")
    else:
        print("✅ Crawler is not currently running")


async def main():
    """Main entry point"""

    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command in ['--help', '-h', 'help']:
            show_help()
            return

        elif command in ['--status', '-s', 'status']:
            show_status()
            return

        elif command in ['--reset', '-r', 'reset']:
            progress_tracker.reset_progress()
            return

        else:
            print(f"❌ Unknown command: {command}")
            print("Use --help for available commands")
            return

    # Start automatic batch crawling
    print("🕷️ RatCrawler - Automatic Batch Mode")
    print("=" * 50)
    print("Features:")
    print("  • Crawls 50 URLs per batch")
    print("  • Saves progress automatically")
    print("  • Resumes from last page on restart")
    print("  • Press Ctrl+C to stop gracefully")
    print()

    # Start background services
    dashboard_process = None
    api_process = None

    try:
        print("🚀 Starting background services...")

        dashboard_process = start_dashboard_background()
        if dashboard_process:
            print("✅ Dashboard starting at http://localhost:8501")

        api_process = start_log_api_background()
        if api_process:
            print("✅ Log API starting at http://localhost:8000")

        print()

        # Log system startup
        log_manager.system_logger.logger.info("RatCrawler Auto Batch Mode started")

        # Run automatic batch crawler
        success = await run_auto_batch_crawler()

        if success:
            print("✅ Batch crawling completed successfully!")
        else:
            print("❌ Batch crawling failed to start")

    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
        log_manager.system_logger.logger.info("RatCrawler Auto Batch Mode stopped by user")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        log_manager.system_logger.logger.error(f"RatCrawler Auto Batch Mode error: {e}")

    finally:
        # Clean up background processes
        if dashboard_process:
            print("👋 Stopping dashboard...")
            dashboard_process.terminate()
            try:
                dashboard_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                dashboard_process.kill()

        if api_process:
            print("👋 Stopping log API...")
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()

        print("👋 Goodbye!")


if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the main function
    asyncio.run(main())
