#!/usr/bin/env python3
"""
Enhanced Run Script for RatCrawler Dashboard
Runs the enhanced dashboard with password authentication
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['streamlit', 'plotly', 'pandas', 'psutil', 'beautifulsoup4']

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        for package in missing_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("✅ All packages installed successfully")

def setup_environment():
    """Setup environment variables"""
    if not os.getenv("DASHBOARD_PASSWORD"):
        os.environ["DASHBOARD_PASSWORD"] = "swadhin"
        print("✅ Dashboard password set to 'swadhin'")

    if not os.getenv("JSONPATH"):
        os.environ["JSONPATH"] = "rat/databases.json"
        print("✅ Database config path set")

def run_dashboard():
    """Run the enhanced Streamlit dashboard"""
    dashboard_path = Path(__file__).parent / "dashboard.py"

    if not dashboard_path.exists():
        print(f"❌ Dashboard file not found: {dashboard_path}")
        return

    print("🕷️ Starting Enhanced RatCrawler Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("🔐 Login credentials: username=swadhin, password=swadhin")
    print("🔄 Press Ctrl+C to stop the dashboard")

    try:
        # Run streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run',
            str(dashboard_path),
            '--server.port', '8501',
            '--server.address', '0.0.0.0'
        ])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")

def main():
    print("🕷️ Enhanced RatCrawler Dashboard Launcher")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("rat").exists():
        print("❌ Please run this script from the RatCrawler root directory")
        sys.exit(1)

    # Setup environment
    setup_environment()

    # Check requirements
    check_requirements()

    # Run dashboard
    run_dashboard()

if __name__ == "__main__":
    main()
