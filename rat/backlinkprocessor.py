import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import networkx as nx
from collections import defaultdict, Counter
import re
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple,Any
import hashlib
from rat.backlinkdb import BacklinkDatabase

@dataclass
class BacklinkData:
    source_url: str
    target_url: str
    anchor_text: str
    context: str
    page_title: str
    domain_authority: float = 0.0
    is_nofollow: bool = False

class BacklinkProcessor:
    def __init__(self, delay=1,usedatabase=True):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BacklinkBot/1.0)'
        })
        self.backlinks = []
        self.link_graph = nx.DiGraph()
        self.domain_scores = {}
        if usedatabase:
            self.database = BacklinkDatabase()
        else:
            self.database = None

    def extract_links_from_page(self, url: str) -> List[BacklinkData]:
        """Extract all outbound links from a given page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            page_title = title_tag.get_text().strip() if title_tag else ""

            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href') if hasattr(link, 'get') else None
                if not href:
                    continue

                absolute_url = urllib.parse.urljoin(url, str(href))

                # Skip non-http links
                if not absolute_url.startswith(('http://', 'https://')):
                    continue

                anchor_text = link.get_text(strip=True) if hasattr(link, 'get_text') else ""
                context = self._extract_context(link)
                rel_attr = link.get('rel') if hasattr(link, 'get') else None
                is_nofollow = bool(rel_attr and 'nofollow' in rel_attr)

                backlink = BacklinkData(
                    source_url=url,
                    target_url=absolute_url,
                    anchor_text=anchor_text,
                    context=context,
                    page_title=page_title,
                    is_nofollow=is_nofollow
                )
                links.append(backlink)

            return links

        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return []

    def _extract_context(self, link_element, context_length=100):
        """Extract surrounding text context for a link"""
        parent = link_element.parent
        if parent:
            text = parent.get_text(strip=True)
            # Find link position and extract context
            link_text = link_element.get_text(strip=True)
            if link_text in text:
                start = max(0, text.find(link_text) - context_length)
                end = min(len(text), text.find(link_text) + len(link_text) + context_length)
                return text[start:end]
        return ""

    def crawl_backlinks(self, seed_urls: List[str], max_depth=2):
        """Crawl and discover backlinks starting from seed URLs"""
        visited = set()
        to_visit = [(url, 0) for url in seed_urls]

        while to_visit:
            current_url, depth = to_visit.pop(0)

            if current_url in visited or depth > max_depth:
                continue

            visited.add(current_url)
            print(f"Processing: {current_url} (depth: {depth})")

            links = self.extract_links_from_page(current_url)
            self.backlinks.extend(links)

            if self.database and links:
                self.database.store_backlinks(links)

            # Add discovered links to crawl queue
            if depth < max_depth:
                for link in links:
                    if link.target_url not in visited:
                        to_visit.append((link.target_url, depth + 1))

            time.sleep(self.delay)

    def build_link_graph(self):
        """Build a directed graph of link relationships"""
        for backlink in self.backlinks:
            self.link_graph.add_edge(
                backlink.source_url,
                backlink.target_url,
                anchor_text=backlink.anchor_text,
                weight=1.0 if not backlink.is_nofollow else 0.1
            )

    def analyze_anchor_text_distribution(self, target_url: str) -> Dict[str, int]:
        """Analyze anchor text distribution for a target URL"""
        anchor_texts = []
        for backlink in self.backlinks:
            if backlink.target_url == target_url and backlink.anchor_text:
                anchor_texts.append(backlink.anchor_text.lower())

        return dict(Counter(anchor_texts))

    def calculate_domain_authority(self):
        """Calculate domain authority based on backlink profile"""
        domain_backlinks = defaultdict(list)

        for backlink in self.backlinks:
            target_domain = urllib.parse.urlparse(backlink.target_url).netloc
            domain_backlinks[target_domain].append(backlink)

        for domain, backlinks in domain_backlinks.items():
            # Simple domain authority calculation
            unique_domains = set()
            total_links = 0
            quality_score = 0

            for backlink in backlinks:
                source_domain = urllib.parse.urlparse(backlink.source_url).netloc
                unique_domains.add(source_domain)
                total_links += 1

                # Quality factors
                if not backlink.is_nofollow:
                    quality_score += 1
                if len(backlink.anchor_text) > 0:
                    quality_score += 0.5
                if backlink.context:
                    quality_score += 0.5

            # Domain authority score (0-100)
            domain_diversity = len(unique_domains)
            authority_score = min(100, (domain_diversity * 2) + (quality_score / total_links * 50))
            self.domain_scores[domain] = authority_score
        if self.database:
            self.database.store_domain_scores(self.domain_scores)
            print(f"Stored domain authority scores for {len(self.domain_scores)} domains")

    def detect_link_spam(self, threshold=0.8) -> List[BacklinkData]:
        """Detect potentially spammy backlinks"""
        spam_links = []

        for backlink in self.backlinks:
            spam_score = 0

            # Check for over-optimization
            if backlink.anchor_text and len(backlink.anchor_text.split()) > 5:
                spam_score += 0.2

            # Check for exact match anchor text patterns
            if backlink.anchor_text and re.search(r'buy|cheap|discount|sale', backlink.anchor_text.lower()):
                spam_score += 0.3

            # Check for suspicious domains
            source_domain = urllib.parse.urlparse(backlink.source_url).netloc
            if any(suspicious in source_domain for suspicious in ['link', 'seo', 'directory']):
                spam_score += 0.4

            # Check for lack of context
            if not backlink.context or len(backlink.context) < 50:
                spam_score += 0.2

            if spam_score >= threshold:
                spam_links.append(backlink)

        return spam_links



    def calculate_pagerank(self, damping_factor=0.85):
        """Calculate PageRank scores for all pages"""
        if not self.link_graph.nodes():
            return {}

        pagerank_scores = nx.pagerank(
            self.link_graph,
            alpha=damping_factor,
            weight='weight'
        )

        # Store PageRank scores in database
        if self.database:
            self.database.store_pagerank_scores(dict(pagerank_scores))
            print("PageRank scores stored in database")

        return pagerank_scores
    def generate_backlink_report(self, target_url: str) -> Dict:
        """Generate comprehensive backlink report for a target URL"""
        target_backlinks = [bl for bl in self.backlinks if bl.target_url == target_url]

        if not target_backlinks:
            return {"error": "No backlinks found for target URL"}

        # Calculate metrics
        total_backlinks = len(target_backlinks)
        unique_domains = len(set(urllib.parse.urlparse(bl.source_url).netloc for bl in target_backlinks))
        nofollow_count = sum(1 for bl in target_backlinks if bl.is_nofollow)

        # Get domain authority
        target_domain = urllib.parse.urlparse(target_url).netloc
        domain_authority = self.domain_scores.get(target_domain, 0)

        # Anchor text analysis
        anchor_distribution = Counter()
        for backlink in target_backlinks:
            if backlink.anchor_text:
                anchor_distribution[backlink.anchor_text.lower()] += 1

        # Top referring domains
        referring_domains = Counter()
        for backlink in target_backlinks:
            domain = urllib.parse.urlparse(backlink.source_url).netloc
            referring_domains[domain] += 1





        return {
            "target_url": target_url,
            "total_backlinks": total_backlinks,
            "unique_referring_domains": unique_domains,
            "nofollow_links": nofollow_count,
            "dofollow_links": total_backlinks - nofollow_count,
            "domain_authority": domain_authority,
            "anchor_text_distribution": dict(anchor_distribution.most_common(10)),
            "top_referring_domains": dict(referring_domains.most_common(10))
        }


# Example usage
def main():
    # Initialize processor
    processor = BacklinkProcessor(delay=1)
    seed_urls = [
       "https://en.wikipedia.org/",
       "https://www.python.org/"
    ]

    print("Starting backlink crawl...")
    processor.crawl_backlinks(seed_urls, max_depth=1)

    print("Building link graph...")
    processor.build_link_graph()

    print("Calculating PageRank...")
    pagerank_scores = processor.calculate_pagerank()

    print("Calculating domain authority...")
    processor.calculate_domain_authority()

    print("Detecting spam links...")
    spam_links = processor.detect_link_spam()

    pagerank_scores = processor.calculate_pagerank()
    print(f"Found {len(processor.link_graph.nodes())} unique pages in link graph")
    print(f"Calculated PageRank for {len(pagerank_scores)} pages")
    print(f"Domain authority scores calculated for {len(processor.domain_scores)} domains")
    print(f"Total backlinks crawled: {len(processor.backlinks)}")
    if spam_links:
        print(f"Detected {len(spam_links)} potential spam links")
    else:
        print("No spam links detected")

    print(f"Found {len(processor.backlinks)} total backlinks")
    print(f"Detected {len(spam_links)} potential spam links")

    # Generate report for a specific URL
    if processor.backlinks:
        sample_url = processor.backlinks[0].target_url
        report = processor.generate_backlink_report(sample_url)
        print(f"\nSample report for {sample_url}:")
        for key, value in report.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()