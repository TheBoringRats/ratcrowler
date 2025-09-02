#!/usr/bin/env python3
"""
Enhanced Backlink Discovery Function for RatCrawler
Improved to handle 401/403 errors with better user agents, retries, and rotation
"""

import json
import asyncio
import aiohttp
import random
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from dataclasses import dataclass
import time
import logging
from .sqlalchemy_database import SQLAlchemyDatabase


@dataclass
class BacklinkData:
    """Data class for backlink information"""
    source_url: str
    target_url: str
    anchor_text: str = ""
    context: str = ""
    page_title: str = ""
    domain_authority: float = 0.0
    is_nofollow: bool = False


class BacklinkDiscoverer:
    """Discovers backlinks from URLs at specified depth with anti-detection measures"""

    def __init__(self, max_depth: int = 4, delay: float = 1.0, respect_robots: bool = False):
        self.max_depth = max_depth
        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.discovered_backlinks: List[BacklinkData] = []
        self.session_timeout = aiohttp.ClientTimeout(total=45)
        self.max_retries = 3
        self.retry_delay = 2.0
        self.respect_robots = respect_robots
        self.robots_checker = create_robots_txt_checker() if respect_robots else None

        # Rotate between multiple realistic user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
        ]

        # Enhanced headers with more browser-like behavior
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def get_random_headers(self) -> Dict[str, str]:
        """Get randomized headers for each request"""
        headers = self.base_headers.copy()
        headers['User-Agent'] = random.choice(self.user_agents)

        # Randomly add some optional headers
        if random.random() > 0.5:
            headers['DNT'] = '1'
        if random.random() > 0.7:
            headers['Sec-GPC'] = '1'

        return headers

    def get_social_media_headers(self, domain: str) -> Dict[str, str]:
        """Get specialized headers for social media domains"""
        headers = self.get_random_headers()

        # Domain-specific header modifications
        if 'linkedin.com' in domain:
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
            })
        elif 'x.com' in domain or 'x.com' in domain:
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
            })
        elif 'facebook.com' in domain:
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
            })
        elif 'youtube.com' in domain:
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
            })

        return headers

    def is_social_media_domain(self, url: str) -> bool:
        """Check if URL is from a social media platform"""
        social_domains = {
            'facebook.com', 'twitter.com', 'x.com', 'instagram.com',
            'linkedin.com', 'pinterest.com', 'youtube.com', 'tiktok.com',
            'snapchat.com', 'reddit.com'
        }
        domain = urlparse(url).netloc.lower()
        return any(social in domain for social in social_domains)

    def load_urls_from_tasks_json(self) -> List[str]:
        """Load URLs from a JSON file"""
        try:
            with open('seed_urls.json', 'r', encoding='utf-8') as file:
                data = json.load(file)

            urls = []

            # Handle different JSON structures
            if isinstance(data, list):
                urls = [url for url in data if isinstance(url, str) and url.startswith(('http://', 'https://'))]
            elif isinstance(data, dict):
                for key in ['urls', 'websites', 'links', 'targets', 'domains', 'tasks']:
                    if key in data and isinstance(data[key], list):
                        urls.extend([url for url in data[key] if isinstance(url, str) and url.startswith(('http://', 'https://'))])

            unique_urls = list(dict.fromkeys(urls))
            print(f"✅ Loaded {len(unique_urls)} unique URLs from seed_urls.json")
            return unique_urls

        except FileNotFoundError:
            print("❌ seed_urls.json file not found.")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format in seed_urls.json: {e}")
            return []
        except Exception as e:
            print(f"❌ Error loading URLs from seed_urls.json: {e}")
            return []

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and crawlable"""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                return False

            # Optional: Skip social media domains (set to False to include them)
            skip_social_media = False  # Change to True if you want to skip them

            if skip_social_media:
                blocked_domains = {
                    'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
                    'pinterest.com', 'youtube.com', 'tiktok.com', 'snapchat.com'
                }

                domain = parsed.netloc.lower()
                if any(blocked in domain for blocked in blocked_domains):
                    return False

            skip_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js',
                             '.xml', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.mp4',
                             '.mp3', '.avi', '.mov', '.ico', '.svg', '.woff', '.ttf'}

            if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
                return False

            return True
        except Exception:
            return False

    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and sorting query parameters"""
        try:
            parsed = urlparse(url)
            parsed = parsed._replace(fragment='')
            if parsed.query:
                query_params = parse_qs(parsed.query, keep_blank_values=True)
                sorted_query = '&'.join(f"{k}={v[0]}" for k, v in sorted(query_params.items()))
                parsed = parsed._replace(query=sorted_query)
            return parsed.geturl()
        except Exception:
            return url

    async def fetch_page_with_retry(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """Fetch a page with retry logic and enhanced error handling"""
        domain = urlparse(url).netloc.lower()
        is_social = self.is_social_media_domain(url)

        # Use longer delays for social media sites
        current_delay = self.delay * 3 if is_social else self.delay

        for attempt in range(self.max_retries):
            try:
                # Use specialized headers for social media
                headers = self.get_social_media_headers(domain) if is_social else self.get_random_headers()

                # Add random delay between retries
                if attempt > 0:
                    retry_delay = current_delay * (attempt + random.uniform(1.0, 2.0))
                    await asyncio.sleep(retry_delay)
                    print(f"🔄 Retry {attempt + 1}/{self.max_retries} for {url}")

                # Social media sites often need special handling
                request_kwargs = {
                    'headers': headers,
                    'timeout': self.session_timeout,
                    'allow_redirects': True,
                    'ssl': False
                }

                # Some social media sites work better with specific settings
                if is_social:
                    request_kwargs['timeout'] = aiohttp.ClientTimeout(total=60)
                    # Add referrer for some social sites
                    if 'linkedin.com' in domain:
                        headers['Referer'] = 'https://www.google.com/'

                async with session.get(url, **request_kwargs) as response:
                    # Handle various HTTP status codes
                    if 200 <= response.status < 300:
                        content = await response.text()
                        return {'url': str(response.url), 'content': content}
                    elif response.status == 429:  # Rate limited
                        wait_time = 10 + random.uniform(0, 10)
                        print(f"⏳ Rate limited for {url}, waiting {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    elif response.status in [401, 403]:
                        if is_social:
                            print(f"🔐 Social media access denied ({response.status}) for {url} - trying different approach...")
                            # For social media, try without certain headers
                            if attempt < self.max_retries - 1:
                                continue
                        print(f"🚫 Access denied ({response.status}) for {url}")
                        if attempt == self.max_retries - 1:
                            return None
                        continue
                    elif response.status == 404:
                        print(f"❌ Not found (404) for {url}")
                        return None
                    elif response.status in [502, 503, 504]:  # Server errors
                        print(f"🔧 Server error ({response.status}) for {url}, retrying...")
                        continue
                    else:
                        print(f"⚠️ HTTP {response.status} for {url}")
                        if attempt == self.max_retries - 1:
                            return None
                        continue

            except aiohttp.ClientError as e:
                print(f"🌐 Network error for {url} (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return None
                continue
            except asyncio.TimeoutError:
                print(f"⏰ Timeout for {url} (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return None
                continue
            except Exception as e:
                print(f"❌ Unexpected error for {url}: {e}")
                return None

        return None

    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """Fetch a single page (wrapper for the retry method)"""
        return await self.fetch_page_with_retry(session, url)

    def extract_links_and_backlinks(self, page_data: Dict, target_domains: Set[str]) -> Tuple[List[str], List[BacklinkData]]:
        """Extract outbound links and identify backlinks pointing to target domains"""
        if not page_data or 'content' not in page_data:
            return [], []

        try:
            soup = BeautifulSoup(page_data['content'], 'html.parser')
            page_title = soup.find('title').get_text(strip=True) if soup.find('title') else ""
            outbound_links, backlinks = [], []

            for link in soup.find_all('a', href=True):
                href = link['href'].strip()
                if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                    continue

                absolute_url = urljoin(page_data['url'], href)
                normalized_url = self.normalize_url(absolute_url)

                if not self.is_valid_url(normalized_url):
                    continue

                # Add any valid, non-visited URL to the crawl queue
                if normalized_url not in self.visited_urls:
                    outbound_links.append(normalized_url)

                # Check if this link is a backlink to one of our target domains
                target_domain = urlparse(normalized_url).netloc
                if target_domain in target_domains:
                    anchor_text = link.get_text(strip=True)
                    # Fixed: Check if rel attribute exists before checking for nofollow
                    rel_attr = link.get('rel', [])
                    if isinstance(rel_attr, str):
                        rel_attr = [rel_attr]
                    is_nofollow = 'nofollow' in rel_attr

                    context = link.parent.get_text(strip=True)[:250] if link.parent else ""

                    backlink = BacklinkData(
                        source_url=page_data['url'],
                        target_url=normalized_url,
                        anchor_text=anchor_text,
                        context=context,
                        page_title=page_title,
                        is_nofollow=is_nofollow
                    )
                    backlinks.append(backlink)

            return outbound_links, backlinks

        except Exception as e:
            print(f"❌ Error parsing page {page_data.get('url', 'Unknown')}: {e}")
            return [], []

    async def crawl_depth(self, session: aiohttp.ClientSession, urls: List[str], current_depth: int, target_domains: Set[str]) -> List[str]:
        """Crawl URLs at current depth with improved error handling"""
        if current_depth > self.max_depth or not urls:
            return []

        print(f"🌀 Crawling depth {current_depth} with {len(urls)} URLs...")
        next_level_urls = set()
        successful_crawls = 0
        failed_crawls = 0

        # Randomize URL order to avoid predictable patterns
        random.shuffle(urls)

        # Limit concurrent requests to avoid overwhelming servers
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

        async def crawl_single_url(url):
            nonlocal successful_crawls, failed_crawls

            if url in self.visited_urls:
                return []

            # Check robots.txt if enabled
            if self.respect_robots and self.robots_checker:
                robots_allowed = await self.robots_checker(session, url)
                if not robots_allowed:
                    print(f"🤖 Robots.txt disallows crawling: {url}")
                    return []

            async with semaphore:
                # Add random delay before each request
                await asyncio.sleep(random.uniform(self.delay * 0.5, self.delay * 1.5))

                page_data = await self.fetch_page(session, url)
                if not page_data:
                    failed_crawls += 1
                    return []

                self.visited_urls.add(page_data['url'])
                successful_crawls += 1
                print(f"📄 Parsed: {page_data['url']} ({successful_crawls}/{successful_crawls + failed_crawls})")

                outbound_links, backlinks = self.extract_links_and_backlinks(page_data, target_domains)
                if backlinks:
                    self.discovered_backlinks.extend(backlinks)

                return outbound_links

        # Process URLs with controlled concurrency
        tasks = [crawl_single_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                next_level_urls.update(result)
            elif isinstance(result, Exception):
                failed_crawls += 1

        print(f"✅ Depth {current_depth} complete. Success: {successful_crawls}, Failed: {failed_crawls}")
        return list(next_level_urls)

    async def discover(self, seed_urls: List[str]) -> List[BacklinkData]:
        """Main backlink discovery method with enhanced session configuration"""
        print(f"🚀 Starting backlink discovery with depth {self.max_depth}")
        target_domains = {urlparse(url).netloc for url in seed_urls}
        print(f"🎯 Targeting domains: {target_domains}")

        # Enhanced session configuration
        connector = aiohttp.TCPConnector(
            limit=10,  # Total connection pool size
            limit_per_host=2,  # Max connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            ssl=False  # Disable SSL verification for problematic sites
        )

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=self.session_timeout,
            trust_env=True  # Use system proxy settings if available
        ) as session:
            current_urls = seed_urls.copy()
            for depth in range(1, self.max_depth + 1):
                if not current_urls:
                    print(f"🏁 No more URLs to crawl at depth {depth}.")
                    break

                next_urls = await self.crawl_depth(session, current_urls, depth, target_domains)
                print(f"📊 Depth {depth} summary: {len(self.discovered_backlinks)} total backlinks discovered")

                # Longer delay between depths to be more respectful
                if depth < self.max_depth and next_urls:
                    depth_delay = random.uniform(3, 7)
                    print(f"⏸️ Waiting {depth_delay:.1f}s before next depth...")
                    await asyncio.sleep(depth_delay)

                current_urls = next_urls

        return self.discovered_backlinks

    def calculate_domain_authority(self, backlinks: List[BacklinkData]) -> Dict[str, float]:
        """Calculate simple domain authority scores based on discovered backlinks"""
        domain_stats = {}
        for backlink in backlinks:
            target_domain = urlparse(backlink.target_url).netloc
            source_domain = urlparse(backlink.source_url).netloc

            if target_domain not in domain_stats:
                domain_stats[target_domain] = {'referring_domains': set(), 'nofollow_count': 0}

            domain_stats[target_domain]['referring_domains'].add(source_domain)
            if backlink.is_nofollow:
                domain_stats[target_domain]['nofollow_count'] += 1

        domain_scores = {}
        for domain, stats in domain_stats.items():
            score = len(stats['referring_domains']) * 1.0 - (stats['nofollow_count'] * 0.25)
            domain_scores[domain] = max(0, round(score, 2))

        return domain_scores


async def main_discover_and_store(depth: int = 4, delay: float = 2.0):
    """Main function to discover and store backlinks with better error handling"""
    print(f"--- Starting Enhanced Backlink Discovery Process ---")
    print(f"🔧 Configuration: Depth={depth}, Base Delay={delay}s, Max Retries=3")

    db_handler = None
    try:
        db_handler = SQLAlchemyDatabase()

        # Test database connectivity before proceeding
        if not db_handler.test_database_connectivity("backlink"):
            print("❌ Database connectivity test failed. Cannot proceed with storage.")
            return False

        discoverer = BacklinkDiscoverer(max_depth=depth, delay=delay)

        seed_urls = discoverer.load_urls_from_tasks_json()
        if not seed_urls:
            print("❌ No valid URLs found. Exiting.")
            return False

        start_time = time.time()
        backlinks = await discoverer.discover(seed_urls)

        print(f"\n--- Discovery Complete ---")
        print(f"⏱️ Time taken: {time.time() - start_time:.2f} seconds")
        print(f"🔗 Total backlinks found: {len(backlinks):,}")
        print(f"🌐 Total URLs visited: {len(discoverer.visited_urls):,}")

        if not backlinks:
            print("🏁 No new backlinks found.")
            return True

        print("📊 Calculating domain authority scores...")
        domain_scores = discoverer.calculate_domain_authority(backlinks)

        # Estimate storage time based on data size
        estimated_minutes = len(backlinks) / 10000  # Rough estimate: 10k records per minute
        if estimated_minutes > 1:
            print(f"⏰ Estimated storage time: {estimated_minutes:.1f} minutes for {len(backlinks):,} backlinks")
            print("� Large dataset detected - using optimized batch processing...")

        print("�💾 Starting backlinks storage in database...")
        storage_start = time.time()
        db_handler.store_backlinks(backlinks)
        storage_time = time.time() - storage_start
        print(f"✅ Backlinks storage completed in {storage_time:.2f} seconds")

        print("💾 Storing domain authority scores...")
        db_handler.store_domain_scores(domain_scores)

        print("\n📈 SUMMARY")
        print("-" * 40)
        print(f"URLs successfully crawled: {len(discoverer.visited_urls):,}")
        print(f"Total processing time: {time.time() - start_time:.2f} seconds")
        print(f"Storage time: {storage_time:.2f} seconds")
        print(f"Domains with new backlinks: {len(domain_scores)}")

        top_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_domains:
            print("\nTop 5 domains by authority score:")
            for domain, score in top_domains:
                print(f"  🏆 {domain}: {score:.2f}")

        return True

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            if db_handler is not None:
                print("🔌 Closing database connections.")
                db_handler.close()
        except (NameError, AttributeError):
            # db_handler wasn't created due to early error or doesn't have close method
            pass


# Additional utility functions for handling blocked sites
def create_robots_txt_checker():
    """Create a simple robots.txt checker to respect website policies"""
    async def check_robots_txt(session: aiohttp.ClientSession, url: str) -> bool:
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    # Basic check for user-agent restrictions
                    if "User-agent: *" in robots_content and "Disallow: /" in robots_content:
                        return False
            return True
        except:
            return True  # If we can't check, assume it's okay

    return check_robots_txt




async def run_discovery():
        success = await main_discover_and_store(depth=2, delay=2.0)
        if success:
            print("🎉 Backlink discovery completed successfully!")
        else:
            print("💥 Backlink discovery failed!")