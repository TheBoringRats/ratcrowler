#!/usr/bin/env python3
"""
Batch-Based Professional Web Crawler for RatCrawler
Processes URLs in small batches (50 URLs per page) to handle large datasets efficiently
"""

import asyncio
import aiohttp
import hashlib
import json
import re
import time
from typing import List, Dict, Set, Optional, Tuple, Generator
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from dataclasses import dataclass
from datetime import datetime
import warnings

# Suppress BeautifulSoup XML parsing warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from .sqlalchemy_database import SQLAlchemyDatabase
from .logger import log_manager


@dataclass
class CrawlResult:
    """Data class for comprehensive crawl results"""
    url: str
    original_url: Optional[str] = None
    redirect_chain: Optional[List[str]] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    content_text: Optional[str] = None
    content_html: Optional[str] = None
    content_hash: Optional[str] = None
    word_count: Optional[int] = None
    page_size: Optional[int] = None
    http_status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    language: Optional[str] = None
    charset: Optional[str] = None
    h1_tags: Optional[List[str]] = None
    h2_tags: Optional[List[str]] = None
    meta_keywords: Optional[List[str]] = None
    canonical_url: Optional[str] = None
    robots_meta: Optional[str] = None
    internal_links_count: Optional[int] = None
    external_links_count: Optional[int] = None
    images_count: Optional[int] = None
    content_type: Optional[str] = None
    file_extension: Optional[str] = None
    crawl_success: bool = False
    error_message: Optional[str] = None


@dataclass
class BatchProgress:
    """Track batch crawling progress"""
    current_page: int = 1
    total_pages: int = 0
    urls_per_page: int = 50
    total_urls: int = 0
    processed_urls: int = 0
    successful_crawls: int = 0
    failed_crawls: int = 0
    start_time: float = 0
    current_batch_time: float = 0


class BatchBacklinkCrawler:
    """
    Professional web crawler that processes URLs in batches from backlinks database
    Designed to handle large datasets efficiently by processing 50 URLs at a time
    """

    def __init__(self, db_handler: SQLAlchemyDatabase, max_concurrent: int = 10, delay: float = 1.0,
                 batch_size: int = 50):
        self.db = db_handler
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.batch_size = batch_size
        self.session_timeout = aiohttp.ClientTimeout(total=30, connect=10)

        # Progress tracking
        self.progress = BatchProgress()
        self.progress.urls_per_page = batch_size

        # Professional browser-like headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

        # Robots.txt cache
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.robots_cache_time: Dict[str, float] = {}

        # Content type mappings
        self.file_extensions = {
            'documents': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf'},
            'archives': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'},
            'media': {'.mp4', '.mp3', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'},
            'images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp', '.tiff'},
            'stylesheets': {'.css', '.scss', '.less'},
            'scripts': {'.js', '.ts', '.coffee'},
            'data': {'.json', '.xml', '.rss', '.csv', '.yaml', '.yml'},
            'fonts': {'.woff', '.woff2', '.ttf', '.eot', '.otf'},
            'other': set()
        }

    def get_total_urls_count(self) -> int:
        """Get total count of unique URLs from backlinks without loading all data"""
        try:
            # Use efficient COUNT query instead of loading all data
            with self.db.get_session("backlink") as session:
                from sqlalchemy import text

                # Count unique URLs from both source and target columns
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
            log_manager.system_logger.log_metric("url_count_error", str(e))
            print(f"❌ Error counting URLs: {e}")
            return 0

    def get_urls_batch(self, page: int, limit: int = 50) -> List[str]:
        """Get a batch of unique URLs from backlinks database using pagination"""
        try:
            offset = (page - 1) * limit

            with self.db.get_session("backlink") as session:
                from sqlalchemy import text

                # Get unique URLs with pagination
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

                # Filter valid URLs
                valid_urls = [url for url in urls if self.is_valid_url(url)]

                log_manager.db_logger.log_db_operation(
                    "batch_fetch", "backlinks",
                    record_count=len(valid_urls),
                    page=page,
                    success=True
                )

                return valid_urls

        except Exception as e:
            log_manager.db_logger.log_db_operation(
                "batch_fetch", "backlinks",
                page=page,
                success=False,
                error=str(e)
            )
            print(f"❌ Error fetching URL batch {page}: {e}")
            return []

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and crawlable"""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                return False

            # Skip query parameters that indicate downloads
            if parsed.query:
                query_params = parse_qs(parsed.query)
                if any(param in query_params for param in ['download', 'attachment']):
                    return False

            return bool(parsed.netloc)
        except Exception:
            return False

    def get_content_type(self, url: str) -> str:
        """Determine content type based on file extension"""
        try:
            parsed = urlparse(url)
            path_lower = parsed.path.lower()

            for content_type, extensions in self.file_extensions.items():
                if any(path_lower.endswith(ext) for ext in extensions):
                    return content_type

            if '.' not in parsed.path or parsed.path.endswith('/'):
                return 'html'
            else:
                return 'other'
        except Exception:
            return 'unknown'

    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and sorting query parameters"""
        try:
            parsed = urlparse(url)
            parsed = parsed._replace(fragment='')
            if parsed.query:
                query_dict = parse_qs(parsed.query)
                sorted_query = '&'.join(f"{k}={v[0]}" for k, v in sorted(query_dict.items()))
                parsed = parsed._replace(query=sorted_query)
            return parsed.geturl()
        except Exception:
            return url

    def can_fetch_url(self, url: str) -> bool:
        """Check robots.txt to see if we can fetch the URL"""
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            cache_key = base_url
            current_time = time.time()

            if cache_key in self.robots_cache_time:
                if current_time - self.robots_cache_time[cache_key] < 86400:  # 24 hours
                    rp = self.robots_cache[cache_key]
                else:
                    rp = RobotFileParser()
                    rp.set_url(f"{base_url}/robots.txt")
                    try:
                        rp.read()
                        self.robots_cache[cache_key] = rp
                        self.robots_cache_time[cache_key] = current_time
                    except Exception:
                        return True
            else:
                rp = RobotFileParser()
                rp.set_url(f"{base_url}/robots.txt")
                try:
                    rp.read()
                    self.robots_cache[cache_key] = rp
                    self.robots_cache_time[cache_key] = current_time
                except Exception:
                    return True

            return rp.can_fetch('*', url)

        except Exception:
            return True

    def extract_page_data(self, html: str, url: str) -> Dict:
        """Extract comprehensive data from HTML content"""
        try:
            parser = 'html.parser'
            if html.strip().startswith('<?xml') or '<rss' in html.lower() or '<feed' in html.lower():
                try:
                    import lxml
                    parser = 'lxml'
                except ImportError:
                    parser = 'html.parser'

            soup = BeautifulSoup(html, parser)

            # Extract title
            title = None
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text()
                if title_text:
                    title = title_text.strip()

            # Extract meta description
            meta_description = None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                content = meta_desc.get('content')
                if content:
                    meta_description = str(content).strip()

            # Extract meta keywords
            meta_keywords = []
            meta_kw = soup.find('meta', attrs={'name': 'keywords'})
            if meta_kw:
                content = meta_kw.get('content')
                if content:
                    content_str = str(content)
                    meta_keywords = [kw.strip() for kw in content_str.split(',') if kw.strip()]

            # Extract canonical URL
            canonical_url = None
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            if canonical:
                href = canonical.get('href')
                if href:
                    canonical_url = str(href)
                    if canonical_url and not canonical_url.startswith(('http://', 'https://')):
                        canonical_url = urljoin(url, canonical_url)

            # Extract robots meta
            robots_meta = None
            robots = soup.find('meta', attrs={'name': 'robots'})
            if robots:
                content = robots.get('content')
                if content:
                    robots_meta = str(content)

            # Extract H1 and H2 tags
            h1_tags = []
            h2_tags = []

            for h1 in soup.find_all('h1'):
                text = h1.get_text()
                if text:
                    h1_tags.append(text.strip())

            for h2 in soup.find_all('h2'):
                text = h2.get_text()
                if text:
                    h2_tags.append(text.strip())

            # Extract text content
            for script in soup(["script", "style"]):
                script.extract()

            content_text = soup.get_text(separator=' ', strip=True)
            word_count = len(content_text.split()) if content_text else 0

            # Extract links
            internal_links = set()
            external_links = set()
            images = set()

            parsed_base = urlparse(url)
            base_domain = parsed_base.netloc

            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href:
                    href_str = str(href)
                    if href_str.startswith(('http://', 'https://')):
                        parsed_href = urlparse(href_str)
                        if parsed_href.netloc == base_domain:
                            internal_links.add(href_str)
                        else:
                            external_links.add(href_str)
                    elif href_str.startswith('/'):
                        internal_links.add(urljoin(url, href_str))

            # Extract images
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    src_str = str(src)
                    if src_str.startswith(('http://', 'https://')):
                        images.add(src_str)
                    elif src_str.startswith('/'):
                        images.add(urljoin(url, src_str))

            # Detect language
            language = None
            html_tag = soup.find('html')
            if html_tag:
                lang = html_tag.get('lang')
                if lang:
                    language = str(lang)[:10]

            return {
                'title': title,
                'meta_description': meta_description,
                'meta_keywords': meta_keywords,
                'canonical_url': canonical_url,
                'robots_meta': robots_meta,
                'h1_tags': h1_tags,
                'h2_tags': h2_tags,
                'content_text': content_text,
                'word_count': word_count,
                'internal_links_count': len(internal_links),
                'external_links_count': len(external_links),
                'images_count': len(images),
                'language': language
            }

        except Exception as e:
            print(f"❌ Error extracting page data from {url}: {e}")
            return {}

    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> CrawlResult:
        """Fetch a single page with comprehensive data extraction"""
        start_time = time.time()
        result = CrawlResult(url=url)

        result.content_type = self.get_content_type(url)
        parsed = urlparse(url)
        if '.' in parsed.path:
            result.file_extension = '.' + parsed.path.split('.')[-1].lower()

        try:
            if not self.can_fetch_url(url):
                result.error_message = "Blocked by robots.txt"
                return result

            async with session.get(url, headers=self.headers, timeout=self.session_timeout,
                                 allow_redirects=True, max_redirects=5) as response:

                result.http_status_code = response.status
                result.response_time_ms = int((time.time() - start_time) * 1000)

                if response.history:
                    result.redirect_chain = [str(h.url) for h in response.history] + [str(response.url)]
                    result.original_url = str(response.history[0].url)

                if response.status != 200:
                    result.error_message = f"HTTP {response.status}"
                    return result

                content = await response.read()

                try:
                    html = content.decode('utf-8')
                    result.charset = 'utf-8'
                except UnicodeDecodeError:
                    try:
                        html = content.decode('latin-1')
                        result.charset = 'latin-1'
                    except UnicodeDecodeError:
                        html = content.decode('utf-8', errors='ignore')
                        result.charset = 'utf-8'

                result.page_size = len(content)
                result.content_html = html
                result.content_hash = hashlib.md5(content).hexdigest()

                if result.content_type == 'html':
                    page_data = self.extract_page_data(html, url)
                    result.__dict__.update(page_data)
                else:
                    result.title = f"{result.content_type.upper()} File: {parsed.path.split('/')[-1]}"
                    result.meta_description = f"File of type: {result.content_type}"
                    if result.file_extension:
                        result.meta_description += f" ({result.file_extension})"
                    result.content_text = f"This is a {result.content_type} file. URL: {url}"

                result.crawl_success = True

        except asyncio.TimeoutError:
            result.error_message = "Timeout"
        except aiohttp.ClientError as e:
            result.error_message = f"Client error: {str(e)}"
        except Exception as e:
            result.error_message = f"Unexpected error: {str(e)}"

        return result

    async def crawl_batch(self, urls: List[str], session_id: int, db_name: str, page_num: int) -> Dict:
        """Crawl a single batch of URLs"""
        print(f"📦 Processing page {page_num}: {len(urls)} URLs")
        log_manager.crawler_logger.log_crawl_start(f"batch-{page_num}", urls, {"batch_size": len(urls)})

        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = []

        async def crawl_with_semaphore(url: str):
            async with semaphore:
                await asyncio.sleep(self.delay)
                async with aiohttp.ClientSession() as session:
                    result = await self.fetch_page(session, url)
                    return result

        batch_start_time = time.time()

        # Process URLs in this batch
        tasks = [crawl_with_semaphore(url) for url in urls]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_count = 0
        failed_count = 0

        for result in batch_results:
            if isinstance(result, Exception):
                print(f"❌ Task error: {result}")
                failed_count += 1
                continue

            results.append(result)

            if isinstance(result, CrawlResult) and result.crawl_success:
                successful_count += 1

                # Log the crawled page
                log_manager.crawler_logger.log_url_crawled(
                    result.url,
                    result.http_status_code or 0,
                    "success",
                    result.response_time_ms or 0
                )

                page_data = {
                    'url': result.url,
                    'original_url': result.original_url,
                    'redirect_chain': result.redirect_chain,
                    'title': result.title,
                    'meta_description': result.meta_description,
                    'content_text': result.content_text,
                    'content_html': result.content_html,
                    'content_hash': result.content_hash,
                    'word_count': result.word_count,
                    'page_size': result.page_size,
                    'http_status_code': result.http_status_code,
                    'response_time_ms': result.response_time_ms,
                    'language': result.language,
                    'charset': result.charset,
                    'h1_tags': result.h1_tags,
                    'h2_tags': result.h2_tags,
                    'meta_keywords': result.meta_keywords,
                    'canonical_url': result.canonical_url,
                    'robots_meta': result.robots_meta,
                    'internal_links_count': result.internal_links_count,
                    'external_links_count': result.external_links_count,
                    'images_count': result.images_count,
                    'content_type': result.content_type,
                    'file_extension': result.file_extension
                }

                try:
                    self.db.store_crawled_page(page_data, session_id, db_name)
                except Exception as e:
                    print(f"❌ Error storing page {result.url}: {e}")
                    failed_count += 1
                    successful_count -= 1
            else:
                failed_count += 1

        batch_time = time.time() - batch_start_time
        self.progress.current_batch_time = batch_time

        # Update progress
        self.progress.processed_urls += len(urls)
        self.progress.successful_crawls += successful_count
        self.progress.failed_crawls += failed_count

        # Progress report
        elapsed_time = time.time() - self.progress.start_time
        urls_per_second = self.progress.processed_urls / elapsed_time if elapsed_time > 0 else 0
        eta_seconds = (self.progress.total_urls - self.progress.processed_urls) / urls_per_second if urls_per_second > 0 else 0

        print(f"✅ Page {page_num} completed: {successful_count} successful, {failed_count} failed")
        print(f"📊 Progress: {self.progress.processed_urls}/{self.progress.total_urls} URLs "
              f"({self.progress.processed_urls/self.progress.total_urls*100:.1f}%)")
        print(f"⏱️  Speed: {urls_per_second:.1f} URLs/sec | ETA: {eta_seconds/60:.1f} minutes")
        print(f"⏱️  Batch time: {batch_time:.1f}s")
        print()

        return {
            'page': page_num,
            'urls_processed': len(urls),
            'successful': successful_count,
            'failed': failed_count,
            'batch_time': batch_time,
            'results': results
        }

    async def run_batch_crawl(self, start_page: int = 1, max_pages: Optional[int] = None) -> Dict:
        """Run batch-based crawl process"""
        print("🔥 Starting Batch-Based Professional Web Crawler")
        print("=" * 60)

        # Initialize progress tracking
        self.progress.start_time = time.time()
        self.progress.current_page = start_page

        # Get total URL count
        print("🔍 Analyzing database size...")
        total_urls = self.get_total_urls_count()

        if total_urls == 0:
            return {'error': 'No URLs found in backlinks database'}

        self.progress.total_urls = total_urls
        self.progress.total_pages = (total_urls + self.batch_size - 1) // self.batch_size

        if max_pages:
            self.progress.total_pages = min(self.progress.total_pages, max_pages)

        print(f"📊 Database Analysis:")
        print(f"   Total URLs: {total_urls:,}")
        print(f"   Batch size: {self.batch_size}")
        print(f"   Total pages: {self.progress.total_pages}")
        print(f"   Starting from page: {start_page}")
        if max_pages:
            print(f"   Max pages to process: {max_pages}")
        print()

        # Create crawl session
        config_data = {
            'crawler_type': 'batch_backlink_based',
            'batch_size': self.batch_size,
            'max_concurrent': self.max_concurrent,
            'delay': self.delay,
            'total_urls': total_urls,
            'start_page': start_page,
            'max_pages': max_pages,
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Create a minimal seed list for session creation
            first_batch = self.get_urls_batch(start_page, min(10, self.batch_size))
            session_id, db_name = self.db.create_crawl_session(first_batch, config_data)
            print(f"✅ Created crawl session {session_id} in database {db_name}")
        except Exception as e:
            return {'error': f'Failed to create crawl session: {e}'}

        try:
            # Process pages in batches
            all_results = []
            total_successful = 0
            total_failed = 0

            for page in range(start_page, start_page + self.progress.total_pages):
                # Get batch of URLs
                batch_urls = self.get_urls_batch(page, self.batch_size)

                if not batch_urls:
                    print(f"📝 No more URLs found at page {page}, ending crawl")
                    break

                # Crawl this batch
                batch_result = await self.crawl_batch(batch_urls, session_id, db_name, page)
                all_results.append(batch_result)

                total_successful += batch_result['successful']
                total_failed += batch_result['failed']

                self.progress.current_page = page

                # Respect rate limiting between batches
                if page < start_page + self.progress.total_pages - 1:  # Not the last page
                    print(f"⏸️  Pausing {self.delay}s between batches...")
                    await asyncio.sleep(self.delay)

            # Finish the session
            self.db.finish_crawl_session(str(session_id), 'completed')

            # Final summary
            total_time = time.time() - self.progress.start_time
            avg_speed = self.progress.processed_urls / total_time if total_time > 0 else 0

            results = {
                'session_id': session_id,
                'db_name': db_name,
                'total_urls_found': total_urls,
                'total_urls_processed': self.progress.processed_urls,
                'total_pages_processed': len(all_results),
                'successful_crawls': total_successful,
                'failed_crawls': total_failed,
                'total_time_seconds': total_time,
                'average_speed_urls_per_second': avg_speed,
                'batch_results': all_results,
                'start_page': start_page,
                'batch_size': self.batch_size
            }

            print("🎉 Batch Crawl Process Completed Successfully!")
            print("=" * 60)
            print(f"📊 Final Results:")
            print(f"   URLs Processed: {self.progress.processed_urls:,}")
            print(f"   Successful: {total_successful:,}")
            print(f"   Failed: {total_failed:,}")
            print(f"   Total Time: {total_time/60:.1f} minutes")
            print(f"   Average Speed: {avg_speed:.1f} URLs/second")
            print(f"   Pages Processed: {len(all_results)}")

            return results

        except Exception as e:
            # Finish session with error status
            try:
                self.db.finish_crawl_session(str(session_id), 'failed')
            except:
                pass
            return {'error': f'Batch crawl failed: {e}'}


async def run_batch_crawler(start_page: int = 1, max_pages: Optional[int] = None,
                           batch_size: int = 50, max_concurrent: int = 10, delay: float = 1.0):
    """
    Main function to run the batch-based crawler

    Args:
        start_page: Page number to start from (1-based)
        max_pages: Maximum number of pages to process (None for all)
        batch_size: Number of URLs per batch/page
        max_concurrent: Maximum concurrent requests
        delay: Delay between requests in seconds
    """
    print("🚀 RatCrawler Batch-Based Professional Crawler")
    print("=" * 60)

    # Initialize database handler
    db_handler = SQLAlchemyDatabase()

    # Create crawler instance
    crawler = BatchBacklinkCrawler(
        db_handler=db_handler,
        max_concurrent=max_concurrent,
        delay=delay,
        batch_size=batch_size
    )

    # Run the batch crawl
    results = await crawler.run_batch_crawl(start_page=start_page, max_pages=max_pages)

    # Print results
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return False
    else:
        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Batch-based Professional Web Crawler')
    parser.add_argument('--start-page', type=int, default=1, help='Page to start from (default: 1)')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to process (default: all)')
    parser.add_argument('--batch-size', type=int, default=50, help='URLs per batch (default: 50)')
    parser.add_argument('--max-concurrent', type=int, default=10, help='Max concurrent requests (default: 10)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (default: 1.0)')

    args = parser.parse_args()

    # Run the crawler
    asyncio.run(run_batch_crawler(
        start_page=args.start_page,
        max_pages=args.max_pages,
        batch_size=args.batch_size,
        max_concurrent=args.max_concurrent,
        delay=args.delay
    ))
