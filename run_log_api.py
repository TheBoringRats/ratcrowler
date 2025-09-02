#!/usr/bin/env python3
"""
Run the RatCrawler Log API Server
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['fastapi', 'uvicorn', 'requests']

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        for package in missing_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("✅ All packages installed successfully")

def run_log_api():
    """Run the FastAPI log server"""
    api_path = Path(__file__).parent / "log_api_server.py"

    if not api_path.exists():
        print(f"❌ Log API file not found: {api_path}")
        return

    print("📡 Starting RatCrawler Log API Server...")
    print("🔗 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop the API server")

    try:
        # Run uvicorn
        subprocess.run([
            sys.executable, str(api_path)
        ])
    except KeyboardInterrupt:
        print("\n🛑 Log API Server stopped")

if __name__ == "__main__":
    check_requirements()
    run_log_api()
