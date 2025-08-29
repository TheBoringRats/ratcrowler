#!/usr/bin/env python3
"""
Test Runner for RatCrawler
Runs all tests from the tests directory
"""

import sys
import os
import subprocess
from pathlib import Path

def run_test(test_file):
    """Run a single test file"""
    print(f"\n🧪 Running {test_file}...")
    print("=" * 50)

    try:
        # Run from the project root directory so imports work correctly
        project_root = Path(__file__).parent
        test_path = project_root / "tests" / test_file

        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=project_root,  # Run from project root
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            print(f"✅ {test_file} passed")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {test_file} failed")
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"⏰ {test_file} timed out")
        return False
    except Exception as e:
        print(f"💥 {test_file} error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 RatCrawler Test Suite")
    print("=" * 60)

    # Get the tests directory
    tests_dir = Path(__file__).parent / "tests"

    if not tests_dir.exists():
        print(f"❌ Tests directory not found: {tests_dir}")
        return False

    # Find all test files
    test_files = []
    for file in tests_dir.glob("test_*.py"):
        if file.name != "__init__.py":
            test_files.append(file.name)

    if not test_files:
        print("❌ No test files found")
        return False

    print(f"📋 Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  • {test_file}")
    print()

    # Run all tests
    passed = 0
    total = len(test_files)

    for test_file in test_files:
        if run_test(test_file):
            passed += 1

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
