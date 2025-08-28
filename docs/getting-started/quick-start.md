---
layout: default
title: Quick Start
nav_order: 3
parent: Getting Started
description: "Get started with RatCrawler in 5 minutes"
---

# Quick Start Guide

Get your first web crawl running in just 5 minutes with RatCrawler.

## Prerequisites

Make sure you have completed the [Installation Guide](installation.md) before proceeding.

## Your First Crawl

### Basic Web Crawling

```python
# basic_crawl.py
from crawler import EnhancedProductionCrawler

# Create a crawler instance
crawler = EnhancedProductionCrawler({
    'delay': 1.5,        # Seconds between requests
    'max_depth': 2,      # How deep to crawl
    'max_pages': 10,     # Maximum pages to crawl
    'user_agent': 'MyBot/1.0'
})

# Crawl a website
urls = ['https://example.com']
results = crawler.comprehensive_crawl(urls)

# Print results
crawler.print_summary(results)
```

**Run the script:**

```bash
python3 basic_crawl.py
```

### Expected Output

```
Crawling Summary:
===============
Total URLs processed: 8
Successful crawls: 7
Failed crawls: 1
Total content size: 45.2 KB
Average response time: 0.8 seconds
```

## Backlink Analysis

### Discover Backlinks

```python
# backlink_analysis.py
from backlinkprocessor import BacklinkProcessor

# Create backlink processor
processor = BacklinkProcessor(
    delay=1.0,
    usedatabase=True
)

# Crawl for backlinks
target_urls = ['https://example.com']
processor.crawl_backlinks(target_urls, max_depth=2)

# Build link graph and calculate PageRank
processor.build_link_graph()
pagerank_scores = processor.calculate_pagerank()

# Print top 5 pages by PageRank
print("Top 5 pages by PageRank:")
for url, score in sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"{score:.4f}: {url}")
```

## Trend Analysis

### Google Trends Analysis

```python
# trend_analysis.py
import sys
sys.path.append('engine')

from googletrends import GoogleTrendsAnalyzer

# Create trends analyzer
analyzer = GoogleTrendsAnalyzer()

# Fetch trending topics
trends = analyzer.fetch_trending_searches(
    country='US',
    limit=5,
    include_summaries=True
)

# Print trending topics
print("Current Trending Topics:")
for i, trend in enumerate(trends, 1):
    print(f"{i}. {trend['title']} (Traffic: {trend.get('traffic', 'N/A')})")
    if 'summary' in trend:
        print(f"   Summary: {trend['summary'][:100]}...")
    print()
```

## Advanced Examples

### Multi-Source Trend Analysis

```python
# multi_source_trends.py
from trend_analyzer import TrendAnalyzer

# Create comprehensive trend analyzer
analyzer = TrendAnalyzer()

# Analyze trends across multiple sources
results = analyzer.analyze_trends(
    keyword="artificial intelligence",
    sources=['google', 'social', 'financial', 'news'],
    time_window='24h'
)

# Generate insights
insights = analyzer.generate_insights(results)

print(f"Trend Score: {insights['trend_score']:.2f}")
print(f"Overall Sentiment: {insights['sentiment']}")
print(f"Peak Activity: {insights['peak_time']}")
```

### Scheduled Crawling

```python
# scheduled_crawler.py
import schedule
import time
from crawler import EnhancedProductionCrawler

def daily_crawl():
    crawler = EnhancedProductionCrawler({
        'max_pages': 50,
        'delay': 2.0,
        'export_json': True
    })

    urls = [
        'https://techcrunch.com',
        'https://news.ycombinator.com',
        'https://github.com/trending'
    ]

    results = crawler.comprehensive_crawl(urls)
    crawler.print_summary(results)
    print(f"Crawl completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Schedule daily crawl at 9 AM
schedule.every().day.at("09:00").do(daily_crawl)

print("Scheduled crawler started. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Database Integration

### Working with SQLite Database

```python
# database_example.py
from crawlerdb import CrawlerDatabase

# Initialize database
db = CrawlerDatabase('crawl_results.db')

# Store crawl results
crawl_data = {
    'url': 'https://example.com',
    'title': 'Example Domain',
    'content': 'This is example content...',
    'word_count': 150,
    'response_time': 0.8
}

db.store_crawl_result(crawl_data)

# Query results
recent_crawls = db.get_recent_crawls(limit=10)
for crawl in recent_crawls:
    print(f"URL: {crawl['url']}")
    print(f"Title: {crawl['title']}")
    print(f"Crawled: {crawl['crawl_date']}")
    print("---")
```

## Rust Version Quick Start

### Basic Rust Crawling

```bash
# Navigate to Rust version
cd rust_version

# Build and run
cargo build --release
./target/release/rat-crawler crawl https://example.com --max-pages 10

# With custom settings
./target/release/rat-crawler crawl https://example.com \
  --max-pages 50 \
  --delay 2 \
  --respect-robots-txt \
  --output results.json
```

## Next Steps

Now that you've completed your first crawls, explore:

1. **[Configuration Guide](configuration.md)** - Customize RatCrawler for your needs
2. **[Web Crawling Features](../features/web-crawling.md)** - Learn advanced crawling techniques
3. **[API Reference](../api-reference/index.md)** - Complete API documentation
4. **[Examples Repository](https://github.com/TheBoringRats/ratcrawler/tree/main/examples)** - More code examples

## Troubleshooting

### Common Issues

**Import Errors:**

```bash
# Make sure you're in the correct directory
cd /path/to/ratcrawler

# Activate virtual environment if used
source venv/bin/activate
```

**Network Errors:**

```python
# Add error handling
try:
    results = crawler.comprehensive_crawl(urls)
except Exception as e:
    print(f"Crawl failed: {e}")
```

**Database Errors:**

```bash
# Check database permissions
ls -la *.db

# Reinitialize database
rm crawl_results.db
python3 -c "from crawlerdb import CrawlerDatabase; CrawlerDatabase('crawl_results.db')"
```

### Getting Help

- 📖 [Full Documentation](https://theboringrats.github.io/ratcrawler/)
- 🐛 [Report Issues](https://github.com/TheBoringRats/ratcrawler/issues)
- 💬 [Discussions](https://github.com/TheBoringRats/ratcrawler/discussions)
- 📧 [Contact](mailto:theboringrats@gmail.com)
