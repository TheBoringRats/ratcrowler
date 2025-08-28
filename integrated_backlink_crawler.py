# integrated_backlink_crawler.py
"""
Integrated Backlink Content Crawler
Combines backlink discovery with content crawling for comprehensive analysis.
"""

import time
from typing import List, Dict, Set
from urllib.parse import urlparse
from backlinkprocessor import BacklinkProcessor, BacklinkData
from crawler import EnhancedProductionCrawler
from crawlerdb import WebsiteCrawlerDatabase
from backlinkdb import BacklinkDatabase

class IntegratedBacklinkContentCrawler:
    """
    Integrated crawler that combines backlink discovery with content crawling.
    Performs comprehensive analysis in three phases:
    1. Discover backlinks from seed URLs
    2. Crawl content from discovered URLs
    3. Generate insights and analysis
    """

    def __init__(self, config: Dict):
        """Initialize the integrated crawler with configuration."""
        self.config = config
        self.delay = config.get('delay', 1.0)
        self.timeout = config.get('timeout', 10)
        self.db_path = config.get('db_path', 'website_crawler.db')

        # Initialize components
        self.backlink_processor = BacklinkProcessor(delay=self.delay, usedatabase=True)
        self.website_db = WebsiteCrawlerDatabase(self.db_path)
        self.backlink_db = BacklinkDatabase()

        # Initialize content crawler
        crawler_config = {
            'delay': self.delay,
            'user_agent': 'Integrated-Backlink-Crawler/1.0',
            'db_path': self.db_path
        }
        self.content_crawler = EnhancedProductionCrawler(crawler_config)

        # Track discovered URLs for content crawling
        self.discovered_urls: Set[str] = set()
        self.backlinks_found: List[BacklinkData] = []
        self.crawled_pages: List[Dict] = []

    def phase1_discover_backlinks(self, seed_urls: List[str]) -> Dict:
        """
        Phase 1: Discover backlinks from seed URLs.

        Returns:
            Dict with discovery summary
        """
        start_time = time.time()

        print("🔍 Phase 1: Discovering backlinks...")

        # Limit depth for testing
        max_depth = 1  # Reduced for faster testing

        # Crawl backlinks from seed URLs
        self.backlink_processor.crawl_backlinks(seed_urls, max_depth=max_depth)

        # Collect discovered URLs and backlinks
        self.backlinks_found = self.backlink_processor.backlinks
        self.discovered_urls = set()

        for backlink in self.backlinks_found:
            self.discovered_urls.add(backlink.source_url)
            self.discovered_urls.add(backlink.target_url)

        # Calculate domains analyzed
        domains_analyzed = len(set(urlparse(url).netloc for url in self.discovered_urls))

        discovery_time = time.time() - start_time

        summary = {
            'total_backlinks_found': len(self.backlinks_found),
            'unique_urls_discovered': len(self.discovered_urls),
            'domains_analyzed': domains_analyzed,
            'discovery_time_seconds': round(discovery_time, 2)
        }

        print(f"✅ Phase 1 complete: {summary['total_backlinks_found']} backlinks from {summary['unique_urls_discovered']} URLs")
        return summary

    def phase2_crawl_content(self) -> Dict:
        """
        Phase 2: Crawl content from discovered URLs.

        Returns:
            Dict with crawling summary
        """
        if not self.discovered_urls:
            return {
                'pages_crawled': 0,
                'successful_crawls': 0,
                'failed_crawls': 0
            }

        print("📄 Phase 2: Crawling content from discovered URLs...")

        # Limit the number of URLs to crawl for testing
        max_urls_to_crawl = 5  # Limit for reasonable testing
        urls_to_crawl = list(self.discovered_urls)[:max_urls_to_crawl]

        successful_crawls = 0
        failed_crawls = 0
        self.crawled_pages = []

        # Simple content crawling without backlink analysis
        for url in urls_to_crawl:
            try:
                page_data = self.content_crawler.crawl_page_content(url)
                if page_data:
                    self.crawled_pages.append(page_data)
                    successful_crawls += 1
                else:
                    failed_crawls += 1
            except Exception as e:
                print(f"❌ Error crawling {url}: {str(e)}")
                failed_crawls += 1

        summary = {
            'pages_crawled': successful_crawls,
            'successful_crawls': successful_crawls,
            'failed_crawls': failed_crawls
        }

        print(f"✅ Phase 2 complete: {summary['pages_crawled']} pages crawled")
        return summary

    def phase3_generate_insights(self, phase1_summary: Dict, phase2_summary: Dict) -> Dict:
        """
        Phase 3: Generate insights from both crawling phases.

        Returns:
            Dict with analysis insights
        """
        print("📊 Phase 3: Generating insights...")

        insights = {
            'backlink_insights': {},
            'content_insights': {},
            'top_domains': []
        }

        # Backlink insights
        if self.backlinks_found:
            # Calculate domain distribution
            domain_counts = {}
            for backlink in self.backlinks_found:
                domain = urlparse(backlink.source_url).netloc
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

            # Top domains by backlink count
            top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            insights['top_domains'] = [{'domain': domain, 'backlinks': count} for domain, count in top_domains]

            insights['backlink_insights'] = {
                'total_backlinks': len(self.backlinks_found),
                'unique_domains': len(domain_counts),
                'avg_backlinks_per_domain': len(self.backlinks_found) / len(domain_counts) if domain_counts else 0
            }

        # Content insights
        if self.crawled_pages:
            total_words = sum(page.get('word_count', 0) for page in self.crawled_pages)
            avg_words = total_words / len(self.crawled_pages) if self.crawled_pages else 0

            insights['content_insights'] = {
                'total_pages': len(self.crawled_pages),
                'avg_word_count': round(avg_words, 1),
                'pages_with_title': sum(1 for page in self.crawled_pages if page.get('title')),
                'pages_with_meta_desc': sum(1 for page in self.crawled_pages if page.get('meta_description'))
            }
        else:
            insights['content_insights'] = {
                'total_pages': 0,
                'avg_word_count': 0,
                'pages_with_title': 0,
                'pages_with_meta_desc': 0
            }

        print(f"✅ Phase 3 complete: Generated insights for {len(insights['top_domains'])} domains")
        return insights
