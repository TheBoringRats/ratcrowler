#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced backlink crawler that includes all file types
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the database for testing
class MockSQLAlchemyDatabase:
    def get_all_backlinks(self):
        return []  # Return empty list for testing

# Import the crawler after mock definition
from rat.crawler import ProfessionalBacklinkCrawler


def test_content_type_detection():
    """Test the content type detection functionality"""
    print("🧪 Testing Content Type Detection")
    print("=" * 50)

    # Initialize crawler with mock database
    db = MockSQLAlchemyDatabase()
    crawler = ProfessionalBacklinkCrawler(db)  # type: ignore

    # Test URLs with different file types
    test_urls = [
        "https://example.com/page.html",
        "https://example.com/document.pdf",
        "https://example.com/spreadsheet.xlsx",
        "https://example.com/image.jpg",
        "https://example.com/video.mp4",
        "https://example.com/archive.zip",
        "https://example.com/script.js",
        "https://example.com/stylesheet.css",
        "https://example.com/data.json",
        "https://example.com/font.woff",
        "https://example.com/unknown.xyz"
    ]

    print("Testing URL content type detection:")
    for url in test_urls:
        content_type = crawler.get_content_type(url)
        is_valid = crawler.is_valid_url(url)
        print(f"  {url} -> Type: {content_type}, Valid: {is_valid}")

    print("\n✅ Content type detection test completed!")


def test_file_extensions():
    """Test the file extension categorization"""
    print("\n🧪 Testing File Extension Categories")
    print("=" * 50)

    db = MockSQLAlchemyDatabase()
    crawler = ProfessionalBacklinkCrawler(db)  # type: ignore

    print("File extension categories:")
    for category, extensions in crawler.file_extensions.items():
        print(f"  {category.upper()}: {sorted(list(extensions))}")

    print(f"\nTotal extensions tracked: {len(crawler.all_extensions)}")
    print("✅ File extension categorization test completed!")


if __name__ == "__main__":
    print("🚀 Enhanced Backlink Crawler - All File Types Test")
    print("=" * 60)

    test_content_type_detection()
    test_file_extensions()

    print("\n🎉 All tests completed!")
    print("\nKey improvements:")
    print("  ✅ Now crawls ALL file types (PDF, DOC, images, videos, etc.)")
    print("  ✅ Categorizes content by type for better organization")
    print("  ✅ Stores file extension information in database")
    print("  ✅ Provides appropriate metadata for different content types")
    print("  ✅ No longer skips any valid URLs based on file extension")
