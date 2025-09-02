#!/usr/bin/env python3
"""
Test script to demonstrate real-time dashboard functionality
"""

import time
import logging
from rat.logger import log_manager

def generate_test_logs():
    """Generate some test logs to demonstrate real-time updates"""
    logger = logging.getLogger("test_realtime")

    print("🧪 Generating test logs for real-time dashboard demo...")
    print("📊 Watch the dashboard update automatically!")

    for i in range(10):
        logger.info(f"Test log entry #{i+1} - Real-time demo")
        if i % 3 == 0:
            logger.warning(f"Test warning #{i//3 + 1} - System check")
        time.sleep(2)  # Wait 2 seconds between logs

    logger.error("Test error - Demo completed!")
    print("✅ Test logs generated. Dashboard should show real-time updates!")

if __name__ == "__main__":
    generate_test_logs()
