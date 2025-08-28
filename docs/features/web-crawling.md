---
layout: default
title: Web Crawling
nav_order: 4
parent: Features
description: "Learn about RatCrawler's web crawling capabilities"
---

# Web Crawling

RatCrawler's web crawling engine is designed for efficient, respectful, and comprehensive website content extraction.

## Core Features

### Recursive Crawling

- **Depth Control**: Configure how deep to crawl (1-10 levels)
- **Breadth Control**: Limit pages per domain or globally
- **Smart Queueing**: Prioritize important pages first

### Content Extraction

- **HTML Parsing**: BeautifulSoup4 for robust HTML parsing
- **Article Extraction**: Newspaper3k for clean article content
- **Metadata Collection**: Title, description, keywords, author
- **Media Detection**: Images, videos, documents

### Respectful Crawling

- **Robots.txt Compliance**: Automatic robots.txt parsing
- **Rate Limiting**: Configurable delays between requests
- **User Agent Rotation**: Multiple user agents for distribution
- **Crawl Delay Respect**: Honors website-specified delays

## Basic Usage

### Simple Website Crawl

```python
from crawler import EnhancedProductionCrawler

# Basic configuration
config = {
    'delay': 1.5,           # Seconds between requests
    'max_depth': 3,         # Maximum crawl depth
    'max_pages': 100,       # Pages per domain
    'user_agent': 'RatCrawler/1.0',
    'respect_robots': True, # Honor robots.txt
    'follow_redirects': True
}

crawler = EnhancedProductionCrawler(config)

# Crawl single website
results = crawler.comprehensive_crawl(['https://example.com'])
crawler.print_summary(results)
```

### Multiple Website Crawl

```python
# Crawl multiple websites
websites = [
    'https://techcrunch.com',
    'https://news.ycombinator.com',
    'https://github.com/trending'
]

results = crawler.comprehensive_crawl(websites)

# Export results
crawler.export_results('crawl_results.json', format='json')
crawler.export_results('crawl_results.csv', format='csv')
```

## Advanced Configuration

### Crawler Configuration Options

```python
advanced_config = {
    # Timing controls
    'delay': 2.0,                    # Base delay between requests
    'random_delay': True,            # Add random delay variation
    'delay_range': (1.0, 3.0),       # Random delay range

    # Depth and breadth controls
    'max_depth': 5,                  # Maximum link depth
    'max_pages_per_domain': 50,      # Pages per domain
    'max_total_pages': 500,          # Total pages across all domains

    # Content filters
    'allowed_domains': ['example.com', 'blog.example.com'],
    'blocked_paths': ['/admin/', '/private/'],
    'content_types': ['text/html', 'application/xhtml+xml'],

    # Extraction settings
    'extract_articles': True,        # Use newspaper3k
    'extract_metadata': True,        # Extract meta tags
    'download_media': False,         # Download images/videos
    'follow_external_links': False,  # Stay within domain

    # Performance settings
    'concurrent_requests': 5,        # Concurrent connections
    'timeout': 30,                   # Request timeout
    'retry_attempts': 3,             # Retry failed requests
    'retry_delay': 5,                # Delay between retries

    # Output settings
    'save_to_database': True,        # Store in SQLite
    'export_json': True,             # Export JSON
    'export_csv': False,             # Export CSV
    'compress_output': True,         # Compress large files

    # Logging and monitoring
    'log_level': 'INFO',             # Logging verbosity
    'progress_bar': True,            # Show progress
    'stats_interval': 10             # Stats update interval
}
```

## Content Types

### Article Extraction

```python
# Extract clean article content
crawler = EnhancedProductionCrawler({'extract_articles': True})

results = crawler.comprehensive_crawl(['https://news-site.com/article'])

for page in results['successful_crawls']:
    if 'article' in page:
        article = page['article']
        print(f"Title: {article['title']}")
        print(f"Authors: {article['authors']}")
        print(f"Publish Date: {article['publish_date']}")
        print(f"Summary: {article['summary'][:200]}...")
        print(f"Content Length: {len(article['text'])} characters")
```

### Metadata Collection

```python
# Collect comprehensive metadata
crawler = EnhancedProductionCrawler({'extract_metadata': True})

results = crawler.comprehensive_crawl(['https://example.com'])

for page in results['successful_crawls']:
    meta = page['metadata']
    print(f"Title: {meta.get('title')}")
    print(f"Description: {meta.get('description')}")
    print(f"Keywords: {meta.get('keywords')}")
    print(f"Author: {meta.get('author')}")
    print(f"Language: {meta.get('language')}")
    print(f"Content Type: {meta.get('content_type')}")
```

## Filtering and Control

### Domain and Path Filtering

```python
# Restrict crawling to specific domains
config = {
    'allowed_domains': [
        'example.com',
        'blog.example.com',
        'docs.example.com'
    ],
    'blocked_paths': [
        '/admin/',
        '/private/',
        '/api/',
        '/wp-admin/'
    ],
    'allowed_extensions': ['.html', '.htm', '.php', '.asp']
}

crawler = EnhancedProductionCrawler(config)
```

### Content Type Filtering

```python
# Only crawl specific content types
config = {
    'content_types': [
        'text/html',
        'application/xhtml+xml',
        'text/plain'
    ],
    'min_content_length': 100,     # Minimum content length
    'max_content_length': 1000000, # Maximum content length
    'require_title': True,         # Must have title tag
    'skip_noindex': True          # Skip pages with noindex meta
}
```

## Robots.txt Compliance

### Automatic Robots.txt Handling

```python
# Robots.txt is automatically respected
config = {
    'respect_robots': True,        # Default: True
    'robots_cache_time': 3600,     # Cache robots.txt for 1 hour
    'crawl_delay_override': None   # Override crawl-delay if needed
}

crawler = EnhancedProductionCrawler(config)

# Check robots.txt for specific URL
allowed = crawler.check_robots_txt('https://example.com/private/')
print(f"Allowed to crawl: {allowed}")
```

### Custom Robots.txt Rules

```python
# Define custom rules for specific domains
custom_robots = {
    'example.com': {
        'disallowed': ['/admin/', '/private/'],
        'crawl_delay': 5,
        'allowed': ['/public/']
    }
}

crawler.set_custom_robots_rules(custom_robots)
```

## Error Handling and Recovery

### Robust Error Handling

```python
# Handle various error scenarios
config = {
    'retry_attempts': 3,
    'retry_delay': 5,
    'retry_backoff': 2.0,          # Exponential backoff
    'timeout': 30,
    'handle_redirects': True,
    'max_redirects': 5
}

crawler = EnhancedProductionCrawler(config)

try:
    results = crawler.comprehensive_crawl(urls)
except Exception as e:
    print(f"Crawl failed: {e}")
    # Implement recovery logic
```

### Monitoring and Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)

# Enable detailed logging
config = {
    'log_level': 'DEBUG',
    'log_requests': True,      # Log each request
    'log_responses': False,    # Log response details
    'log_errors': True,        # Log errors
    'stats_interval': 30       # Update stats every 30 seconds
}
```

## Performance Optimization

### Concurrent Crawling

```python
# Optimize for performance
config = {
    'concurrent_requests': 10,      # Concurrent connections
    'delay': 1.0,                  # Base delay
    'batch_size': 50,              # Process URLs in batches
    'connection_pool_size': 20,    # Connection pool
    'keep_alive': True,            # Keep connections alive
    'compression': True            # Enable compression
}

crawler = EnhancedProductionCrawler(config)
```

### Memory Management

```python
# Control memory usage
config = {
    'max_memory_mb': 512,          # Memory limit
    'cleanup_interval': 100,       # Cleanup every 100 pages
    'cache_size': 1000,            # URL cache size
    'content_cache': True,         # Cache page content
    'compress_cache': True         # Compress cached content
}
```

## Database Integration

### SQLite Storage

```python
from crawlerdb import CrawlerDatabase

# Initialize database
db = CrawlerDatabase('crawl_results.db')

# Configure crawler to use database
config = {
    'save_to_database': True,
    'database_path': 'crawl_results.db',
    'batch_insert_size': 100,      # Insert in batches
    'vacuum_on_complete': True     # Optimize database
}

crawler = EnhancedProductionCrawler(config)
crawler.set_database(db)
```

### Querying Results

```python
# Query crawl results
recent_pages = db.get_recent_crawls(limit=10)
domain_stats = db.get_domain_statistics()
failed_crawls = db.get_failed_crawls()

# Advanced queries
pages_with_keyword = db.search_content('artificial intelligence')
pages_by_date = db.get_crawls_by_date_range('2024-01-01', '2024-01-31')
```

## Export and Integration

### Multiple Export Formats

```python
# Export in multiple formats
crawler.export_results('results.json', format='json')
crawler.export_results('results.csv', format='csv')
crawler.export_results('results.xml', format='xml')

# Custom export
def custom_exporter(results, filename):
    with open(filename, 'w') as f:
        for page in results['successful_crawls']:
            f.write(f"URL: {page['url']}\n")
            f.write(f"Title: {page['title']}\n")
            f.write(f"Content Length: {len(page['content'])}\n")
            f.write("-" * 50 + "\n")

custom_exporter(results, 'custom_export.txt')
```

## Best Practices

### Ethical Crawling

1. **Respect robots.txt** - Always check and honor robots.txt files
2. **Use appropriate delays** - Don't overwhelm servers
3. **Identify your crawler** - Use descriptive user agents
4. **Limit concurrent requests** - Be considerate of server resources
5. **Handle errors gracefully** - Don't retry excessively on failures

### Performance Tips

1. **Use appropriate concurrency** - Balance speed with server load
2. **Implement caching** - Cache DNS lookups and content
3. **Batch operations** - Process URLs in batches for efficiency
4. **Monitor resources** - Track memory and CPU usage
5. **Use compression** - Enable gzip/deflate when possible

### Maintenance

1. **Regular cleanup** - Remove old crawl data periodically
2. **Update dependencies** - Keep libraries up to date
3. **Monitor logs** - Review logs for issues and patterns
4. **Backup data** - Regularly backup crawl databases
5. **Test configurations** - Validate settings before large crawls

## Troubleshooting

### Common Issues

**High Memory Usage:**

```python
# Reduce memory footprint
config = {
    'max_memory_mb': 256,
    'cleanup_interval': 50,
    'content_cache': False
}
```

**Slow Crawling:**

```python
# Optimize for speed
config = {
    'concurrent_requests': 20,
    'delay': 0.5,
    'timeout': 10
}
```

**Connection Errors:**

```python
# Improve connection reliability
config = {
    'retry_attempts': 5,
    'timeout': 60,
    'keep_alive': True
}
```

## Next Steps

- [Backlink Analysis](backlink-analysis.md) - Discover and analyze backlinks
- [Trend Analysis](trend-analysis.md) - Multi-source trend monitoring
- [API Reference](../api-reference/index.md) - Complete API documentation
- [Performance Tuning](../advanced/performance-tuning.md) - Optimize for large-scale crawling
