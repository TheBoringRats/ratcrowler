# enhanced_production_crawler.py
import time
import json
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Optional, Tuple
import hashlib
from datetime import datetime
from urllib.robotparser import RobotFileParser
import heapq
import warnings
from bs4 import XMLParsedAsHTMLWarning

# Suppress XML parsing warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from backlinkprocessor import BacklinkProcessor, BacklinkData
from crawlerdb import WebsiteCrawlerDatabase

class EnhancedProductionCrawler:
    """
    Enhanced production crawler that combines website content crawling
    with backlink analysis and stores everything in a comprehensive database.
    Improved to emulate large search engine behaviors: robots.txt compliance,
    dynamic crawl delays, redirect chains, content deduplication, priority-based crawling,
    persistent visited URLs/hashes, and incremental recrawling.
    """

    def __init__(self, config: Dict):
        """Initialize the enhanced crawler."""
        self.config = config
        self.database = WebsiteCrawlerDatabase(config.get('db_path', 'website_crawler.db'))
        self.backlink_processor = BacklinkProcessor(
            delay=config.get('delay', 1),
            usedatabase=False  # We'll handle database ourselves
        )

        # Load persistent state from database
        self.visited_urls: Set[str] = set(self.database.get_all_crawled_urls() or [])
        self.content_hashes: Set[str] = set(self.database.get_all_content_hashes() or [])
        self.robot_parsers: Dict[str, Optional[RobotFileParser]] = {}

        # Priority queue for URLs: (priority, url) where lower priority number = higher priority
        self.url_frontier: List[Tuple[float, str]] = []

        # Crawling state
        self.session_id = None
        self.crawled_pages = []

        # Setup session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('user_agent', 'Enhanced-Web-Crawler/1.0 (+https://example.com/crawler-info)'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def safe_get_attr(self, element, attr: str, default: str = '') -> str:
        """Safely get an attribute from a BeautifulSoup element."""
        if element and hasattr(element, 'get'):
            value = element.get(attr, default)
            return str(value) if value is not None else default
        return default

    def safe_get_text(self, element) -> str:
        """Safely get text from a BeautifulSoup element."""
        if element and hasattr(element, 'get_text'):
            return element.get_text(strip=True)
        return ''

    def start_crawl_session(self, seed_urls: List[str]) -> str:
        """Start a new crawl session."""
        self.session_id = self.database.create_crawl_session(seed_urls, self.config)
        print(f"🚀 Started crawl session: {self.session_id}")

        # Add seeds to priority queue with initial priority
        for url in seed_urls:
            if url not in self.visited_urls:
                heapq.heappush(self.url_frontier, (0.0, url))  # Priority 0 for seeds

        return self.session_id

    def get_robot_parser(self, url: str) -> Optional[RobotFileParser]:
        """Fetch and cache robots.txt parser for a domain."""
        parsed = urlparse(url)
        domain = parsed.netloc
        scheme = parsed.scheme

        if domain not in self.robot_parsers:
            robots_url = f"{scheme}://{domain}/robots.txt"
            try:
                # Try to fetch robots.txt with a timeout
                import urllib.request
                import urllib.error

                req = urllib.request.Request(robots_url)
                req.add_header('User-Agent', str(self.session.headers['User-Agent']))

                with urllib.request.urlopen(req, timeout=5) as response:
                    parser = RobotFileParser()
                    parser.set_url(robots_url)
                    parser.read()
                    self.robot_parsers[domain] = parser

            except Exception as e:
                print(f"⚠️ Failed to fetch robots.txt for {domain}: {str(e)}")
                self.robot_parsers[domain] = None

        return self.robot_parsers.get(domain)

    def needs_recrawl(self, url: str) -> bool:
        """Check if a visited URL needs to be recrawled based on age."""
        last_crawl = self.database.get_last_crawl_time(url)
        if not last_crawl:
            return True
        days_since = (datetime.now() - datetime.fromisoformat(last_crawl)).days
        return days_since >= self.config.get('recrawl_days', 7)

    def crawl_page_content(self, url: str) -> Optional[Dict]:
        """
        Crawl a single page and extract comprehensive content data.
        Respects robots.txt, handles redirects, detects duplicate content via hash,
        and supports incremental recrawling.

        Returns:
            Dict with page content data or None if crawling failed, blocked, or skipped
        """
        if url in self.visited_urls and not self.needs_recrawl(url):
            print(f"⏭️ Skipping recent crawl: {url}")
            return None

        # Check robots.txt
        parser = self.get_robot_parser(url)
        user_agent = str(self.session.headers['User-Agent'])
        if parser and not parser.can_fetch(user_agent, url):
            error_msg = "Blocked by robots.txt"
            print(f"🚫 {error_msg}: {url}")
            if self.session_id:
                self.database.log_crawl_error(self.session_id, url, "ROBOTS_BLOCKED", error_msg)
            return None

        try:
            start_time = time.time()

            print(f"📄 Crawling page: {url}")
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()

            # Handle redirects
            original_url = url
            url = response.url
            if url != original_url:
                if url in self.visited_urls and not self.needs_recrawl(url):
                    return None
                print(f"🔀 Redirected to: {url}")

            response_time = int((time.time() - start_time) * 1000)

            # Content hash for deduplication
            content_hash = hashlib.md5(response.content).hexdigest()
            if content_hash in self.content_hashes:
                print(f"📑 Duplicate content detected: {url}")
                return None
            self.content_hashes.add(content_hash)

            # Parse content with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'meta', 'link']):
                script.decompose()

            # Extract basic page data
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ""

            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_description = meta_desc.get('content', '') if meta_desc and hasattr(meta_desc, 'get') else ""

            # Meta keywords
            meta_keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            meta_keywords = meta_keywords_tag.get('content', '') if meta_keywords_tag and hasattr(meta_keywords_tag, 'get') else ""

            # Canonical URL
            canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
            canonical_url = canonical_tag.get('href', '') if canonical_tag and hasattr(canonical_tag, 'get') else ""
            if canonical_url and canonical_url != url:
                if canonical_url in self.visited_urls and not self.needs_recrawl(canonical_url):
                    return None
                print(f"📌 Canonical URL: {canonical_url}")

            # Robots meta
            robots_tag = soup.find('meta', attrs={'name': 'robots'})
            robots_meta = robots_tag.get('content', '') if robots_tag and hasattr(robots_tag, 'get') else ""
            if 'noindex' in str(robots_meta).lower():
                print(f"🚫 Noindex meta tag: {url}")
                return None

            # Extract headings
            h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
            h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]

            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)

            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = ' '.join(chunk for chunk in chunks if chunk)

            # Count elements
            internal_links = 0
            external_links = 0
            base_domain = urlparse(url).netloc

            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and hasattr(href, '__str__'):
                    full_url = urljoin(url, str(href))
                    link_domain = urlparse(full_url).netloc

                    if link_domain == base_domain:
                        internal_links += 1
                    else:
                        external_links += 1

            images_count = len(soup.find_all('img'))

            # Detect language (simple heuristic)
            html_tag = soup.find('html')
            language = html_tag.get('lang', '') if html_tag and hasattr(html_tag, 'get') else ""

            # Detect charset
            charset = response.encoding or 'utf-8'

            # Redirect chain
            redirect_chain = [r.url for r in response.history] + [url]

            # Create page data structure
            page_data = {
                'url': url,
                'original_url': original_url,
                'redirect_chain': redirect_chain,
                'title': title_text,
                'meta_description': meta_description,
                'content_text': text_content,
                'content_html': response.text,
                'content_hash': content_hash,
                'word_count': len(text_content.split()),
                'page_size': len(response.content),
                'http_status_code': response.status_code,
                'response_time_ms': response_time,
                'language': language,
                'charset': charset,
                'h1_tags': h1_tags,
                'h2_tags': h2_tags,
                'meta_keywords': meta_keywords,
                'canonical_url': canonical_url,
                'robots_meta': robots_meta,
                'internal_links_count': internal_links,
                'external_links_count': external_links,
                'images_count': images_count,
                'crawl_time': datetime.now().isoformat()
            }

            # Store in database
            if self.session_id:
                self.database.store_crawled_page(page_data, self.session_id)

            # Mark as visited and update hashes
            self.visited_urls.add(url)
            if canonical_url:
                self.visited_urls.add(str(canonical_url))
            self.crawled_pages.append(page_data)

            return page_data

        except requests.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            print(f"❌ Error crawling {url}: {error_msg}")

            if self.session_id:
                self.database.log_crawl_error(
                    self.session_id, url, "HTTP_ERROR", error_msg,
                    getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                )
            return None

        except Exception as e:
            error_msg = f"Parsing failed: {str(e)}"
            print(f"❌ Error processing {url}: {error_msg}")

            if self.session_id:
                self.database.log_crawl_error(
                    self.session_id, url, "PARSE_ERROR", error_msg
                )
            return None

        finally:
            # Respect crawl delay (max of config and robots.txt)
            delay = self.config.get('delay', 1)
            if parser:
                cd = parser.crawl_delay(user_agent)
                if cd is not None:
                    delay = max(delay, float(cd))
            time.sleep(delay)

    def discover_links(self, url: str, html_content: str) -> List[Tuple[float, str]]:
        """Discover links from a page for further crawling, with priority scores."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []

        base_domain = urlparse(url).netloc

        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and hasattr(href, '__str__'):
                # Convert to absolute URL
                absolute_url = urljoin(url, str(href))

                # Filter links based on configuration
                if self.is_valid_crawl_url(absolute_url, base_domain):
                    # Simple priority: lower for internal, higher for external
                    priority = 1.0 if urlparse(absolute_url).netloc == base_domain else 2.0
                    links.append((priority, absolute_url))

        return links

    def is_valid_crawl_url(self, url: str, base_domain: str) -> bool:
        """Check if URL should be crawled."""
        try:
            parsed = urlparse(url)

            # Basic validation
            if not parsed.scheme or not parsed.netloc:
                return False

            # Only HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False

            # Skip certain file types
            skip_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.exe', '.mp4', '.avi'}
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False

            # Skip if already visited and doesn't need recrawl
            if url in self.visited_urls and not self.needs_recrawl(url):
                return False

            # Domain restrictions
            if self.config.get('stay_on_domain', True):
                return parsed.netloc == base_domain

            # Allow external domains if specified
            allowed_domains = self.config.get('allowed_domains', [])
            if allowed_domains:
                return parsed.netloc in allowed_domains

            return True

        except Exception:
            return False

    def comprehensive_crawl(self, seed_urls: List[str]) -> Dict:
        """
        Execute comprehensive crawling and analysis using a priority queue frontier.
        Supports recursive discovery and backlink collection.

        Returns:
            Dict with complete analysis results
        """
        start_time = time.time()

        # Start crawl session and initialize frontier
        self.start_crawl_session(seed_urls)

        print(f"🔍 Starting comprehensive crawl of {len(seed_urls)} seed URLs")
        print(f"Configuration: {self.config}")
        print("-" * 60)

        try:
            # Phase 1: Website Content Crawling with priority frontier
            print("📊 Phase 1: Crawling website content...")
            max_pages = self.config.get('max_pages', 100)
            max_depth = self.config.get('max_depth', 3)  # Increased for more recursion
            current_depth = 0

            while self.url_frontier and len(self.crawled_pages) < max_pages and current_depth <= max_depth:
                priority, url = heapq.heappop(self.url_frontier)

                page_data = self.crawl_page_content(url)

                if page_data:
                    # Discover new links and add to frontier with adjusted priority
                    discovered_links = self.discover_links(url, page_data['content_html'])
                    for new_priority, link in discovered_links:
                        adjusted_priority = new_priority + current_depth
                        if link not in self.visited_urls or self.needs_recrawl(link):
                            heapq.heappush(self.url_frontier, (adjusted_priority, link))

                if len(self.crawled_pages) % 10 == 0:
                    current_depth += 1

            print(f"✅ Phase 1 complete: {len(self.crawled_pages)} pages crawled")

            # Phase 2: Backlink Analysis (optional)
            if self.config.get('analyze_backlinks', False):
                print("📊 Phase 2: Analyzing backlinks...")

                crawled_urls = [page['url'] for page in self.crawled_pages]
                # Limit backlink analysis to avoid timeouts
                analysis_urls = crawled_urls[:5]  # Limit to first 5 URLs
                self.backlink_processor.crawl_backlinks(analysis_urls, max_depth=1)  # Reduced depth

                # Store backlinks in database
                if self.backlink_processor.backlinks and self.session_id:
                    self.database.store_backlinks(self.backlink_processor.backlinks, self.session_id)

                # Build link graph and calculate metrics
                self.backlink_processor.build_link_graph()
                pagerank_scores = self.backlink_processor.calculate_pagerank()
                self.backlink_processor.calculate_domain_authority()
                spam_links = self.backlink_processor.detect_link_spam()

                # Store analysis results
                if pagerank_scores:
                    self.database.store_pagerank_scores(dict(pagerank_scores))

                if self.backlink_processor.domain_scores:
                    self.database.store_domain_stats(self.backlink_processor.domain_scores)

                print(f"✅ Phase 2 complete: {len(self.backlink_processor.backlinks)} backlinks analyzed")
            else:
                print("📊 Phase 2: Skipping backlink analysis (use analyze_backlinks=True to enable)")
                pagerank_scores = {}
                spam_links = []

            # Optional: Add discovered backlink sources/targets to frontier for further recursion
            for bl in self.backlink_processor.backlinks:
                if self.is_valid_crawl_url(bl.source_url, urlparse(seed_urls[0]).netloc):
                    heapq.heappush(self.url_frontier, (3.0, bl.source_url))  # Higher priority for backlink sources
                if self.is_valid_crawl_url(bl.target_url, urlparse(seed_urls[0]).netloc):
                    heapq.heappush(self.url_frontier, (3.0, bl.target_url))

            # Phase 3: Generate Results
            print("📊 Phase 3: Compiling results...")

            analysis_time = time.time() - start_time

            results = {
                'session_id': self.session_id,
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'analysis_time_seconds': round(analysis_time, 2),
                'configuration': self.config,
                'seed_urls': seed_urls,

                'pages_crawled': len(self.crawled_pages),
                'total_words': sum(page.get('word_count', 0) for page in self.crawled_pages),
                'avg_page_size': sum(page.get('page_size', 0) for page in self.crawled_pages) / len(self.crawled_pages) if self.crawled_pages else 0,
                'unique_domains_crawled': len(set(urlparse(page['url']).netloc for page in self.crawled_pages)),

                'backlinks_found': len(self.backlink_processor.backlinks),
                'internal_links': sum(1 for bl in self.backlink_processor.backlinks if urlparse(bl.source_url).netloc == urlparse(bl.target_url).netloc),
                'external_links': sum(1 for bl in self.backlink_processor.backlinks if urlparse(bl.source_url).netloc != urlparse(bl.target_url).netloc),
                'nofollow_links': sum(1 for bl in self.backlink_processor.backlinks if bl.is_nofollow),
                'spam_links_detected': len(spam_links),

                'avg_word_count': sum(page.get('word_count', 0) for page in self.crawled_pages) / len(self.crawled_pages) if self.crawled_pages else 0,
                'pages_with_meta_description': sum(1 for page in self.crawled_pages if page.get('meta_description')),
                'pages_with_h1_tags': sum(1 for page in self.crawled_pages if page.get('h1_tags')),

                'sample_pages': [
                    {
                        'url': page['url'],
                        'title': page.get('title', '')[:100],
                        'word_count': page.get('word_count', 0),
                        'response_time_ms': page.get('response_time_ms', 0)
                    }
                    for page in self.crawled_pages[:5]
                ],

                'top_domains_by_authority': dict(
                    sorted(self.backlink_processor.domain_scores.items(),
                          key=lambda x: x[1], reverse=True)[:10]
                ) if self.backlink_processor.domain_scores else {},

                'database_summary': self.database.get_crawl_summary(self.session_id) if self.session_id else {}
            }

            # Mark session as completed
            if self.session_id:
                self.database.finish_crawl_session(self.session_id, 'completed')

            print(f"✅ Phase 3 complete: Comprehensive analysis finished")

            return results

        except Exception as e:
            error_msg = f"Crawl failed: {str(e)}"
            print(f"❌ {error_msg}")

            if self.session_id:
                self.database.finish_crawl_session(self.session_id, 'failed')

            return {
                'session_id': self.session_id,
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'pages_crawled': len(self.crawled_pages),
                'analysis_time_seconds': time.time() - start_time
            }

    def export_results(self, results: Dict):
        """Export crawl results to files."""
        timestamp = int(time.time())

        # Export JSON results
        if self.config.get('export_json', False):
            json_filename = f"crawl_results_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            print(f"📄 Results exported to {json_filename}")

        # Export CSV data
        if self.config.get('export_csv', False):
            # Export pages data
            pages_filename = f"crawled_pages_{timestamp}.csv"
            self.database.export_data(pages_filename, 'csv', 'crawled_pages')

            # Export backlinks data
            backlinks_filename = f"backlinks_{timestamp}.csv"
            self.database.export_data(backlinks_filename, 'csv', 'backlinks')

            print(f"📄 CSV data exported to {pages_filename} and {backlinks_filename}")

    def print_summary(self, results: Dict):
        """Print formatted summary of crawl results."""
        if not results.get('success'):
            print(f"❌ Crawl failed: {results.get('error', 'Unknown error')}")
            return

        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE CRAWL SUMMARY")
        print("=" * 60)

        print(f"Session ID: {results['session_id']}")
        print(f"Analysis time: {results['analysis_time_seconds']:.1f} seconds")
        print(f"Pages crawled: {results['pages_crawled']}")
        print(f"Total words: {results['total_words']:,}")
        print(f"Unique domains: {results['unique_domains_crawled']}")
        print(f"Backlinks found: {results['backlinks_found']}")
        print(f"Internal links: {results['internal_links']}")
        print(f"External links: {results['external_links']}")
        print(f"NoFollow links: {results['nofollow_links']}")
        print(f"Spam links: {results['spam_links_detected']}")

        print(f"\n📈 Quality Metrics:")
        print(f"Average words per page: {results['avg_word_count']:.0f}")
        print(f"Pages with meta description: {results['pages_with_meta_description']}")
        print(f"Pages with H1 tags: {results['pages_with_h1_tags']}")

        if results['sample_pages']:
            print(f"\n📄 Sample Pages:")
            for page in results['sample_pages']:
                print(f"  {page['url'][:60]}... ({page['word_count']} words, {page['response_time_ms']}ms)")

        if results['top_domains_by_authority']:
            print(f"\n🏆 Top Domains by Authority:")
            for domain, score in list(results['top_domains_by_authority'].items())[:5]:
                print(f"  {domain}: {score:.1f}")

    def get_all_backlinks(self) -> List[Dict]:
        """Retrieve all backlinks from the database."""
        return self.database.get_all_backlinks()