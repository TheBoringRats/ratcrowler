---
layout: default
title: API Reference
nav_order: 6
description: "Complete API reference for RatCrawler"
---

# API Reference

This section provides comprehensive documentation for RatCrawler's Python and Rust APIs.

## Python API

### EnhancedProductionCrawler

The main crawler class for comprehensive web crawling operations.

#### Constructor

```python
EnhancedProductionCrawler(config: dict = None)
```

**Parameters:**

- `config` (dict, optional): Configuration dictionary with crawler settings

**Example:**

```python
from crawler import EnhancedProductionCrawler

config = {
    'delay': 1.5,
    'max_depth': 3,
    'max_pages': 100,
    'user_agent': 'RatCrawler/1.0'
}

crawler = EnhancedProductionCrawler(config)
```

#### Methods

##### comprehensive_crawl(urls, \*\*kwargs)

Perform a comprehensive crawl of specified URLs.

```python
comprehensive_crawl(urls: list, **kwargs) -> dict
```

**Parameters:**

- `urls` (list): List of URLs to crawl
- `**kwargs`: Additional configuration overrides

**Returns:**

- `dict`: Crawl results with statistics and data

**Example:**

```python
results = crawler.comprehensive_crawl([
    'https://example.com',
    'https://news-site.com'
])

print(f"Successful: {results['successful_crawls']}")
print(f"Failed: {results['failed_crawls']}")
```

##### crawl_single_url(url, \*\*kwargs)

Crawl a single URL with detailed control.

```python
crawl_single_url(url: str, **kwargs) -> dict
```

**Parameters:**

- `url` (str): URL to crawl
- `**kwargs`: Configuration overrides

**Returns:**

- `dict`: Detailed crawl result for the URL

##### print_summary(results)

Print a formatted summary of crawl results.

```python
print_summary(results: dict) -> None
```

**Parameters:**

- `results` (dict): Crawl results from comprehensive_crawl()

##### export_results(filename, format='json')

Export crawl results to file.

```python
export_results(filename: str, format: str = 'json') -> None
```

**Parameters:**

- `filename` (str): Output filename
- `format` (str): Export format ('json', 'csv', 'xml')

### BacklinkProcessor

Class for discovering and analyzing backlinks.

#### Constructor

```python
BacklinkProcessor(delay: float = 1.0, usedatabase: bool = True)
```

**Parameters:**

- `delay` (float): Delay between requests in seconds
- `usedatabase` (bool): Whether to use database storage

#### Methods

##### crawl_backlinks(urls, max_depth=2)

Crawl websites to discover backlinks.

```python
crawl_backlinks(urls: list, max_depth: int = 2) -> None
```

**Parameters:**

- `urls` (list): Target URLs to find backlinks for
- `max_depth` (int): Maximum crawl depth

##### build_link_graph()

Build internal link graph from crawled data.

```python
build_link_graph() -> None
```

##### calculate_pagerank(damping_factor=0.85)

Calculate PageRank scores for all discovered URLs.

```python
calculate_pagerank(damping_factor: float = 0.85) -> dict
```

**Parameters:**

- `damping_factor` (float): PageRank damping factor

**Returns:**

- `dict`: URL to PageRank score mapping

##### get_domain_authority(domain)

Get authority score for a domain.

```python
get_domain_authority(domain: str) -> float
```

**Parameters:**

- `domain` (str): Domain to analyze

**Returns:**

- `float`: Domain authority score (0-100)

### CrawlerDatabase

Database management for crawl results.

#### Constructor

```python
CrawlerDatabase(db_path: str = 'crawler.db')
```

**Parameters:**

- `db_path` (str): Path to SQLite database file

#### Methods

##### store_crawl_result(data)

Store crawl result in database.

```python
store_crawl_result(data: dict) -> int
```

**Parameters:**

- `data` (dict): Crawl result data

**Returns:**

- `int`: Row ID of inserted record

##### get_recent_crawls(limit=100)

Get recently crawled pages.

```python
get_recent_crawls(limit: int = 100) -> list
```

**Parameters:**

- `limit` (int): Maximum number of results

**Returns:**

- `list`: List of crawl records

##### search_content(keyword)

Search crawled content for keyword.

```python
search_content(keyword: str) -> list
```

**Parameters:**

- `keyword` (str): Search keyword

**Returns:**

- `list`: Matching content records

## Trend Analysis API

### TrendAnalyzer

Multi-source trend analysis engine.

#### Constructor

```python
TrendAnalyzer()
```

#### Methods

##### analyze_trends(keyword, sources, time_window)

Analyze trends across multiple sources.

```python
analyze_trends(keyword: str, sources: list, time_window: str) -> dict
```

**Parameters:**

- `keyword` (str): Keyword to analyze
- `sources` (list): List of sources ('google', 'social', 'financial', 'news')
- `time_window` (str): Time window ('1h', '24h', '7d', '30d')

**Returns:**

- `dict`: Comprehensive trend analysis

##### generate_insights(analysis_results)

Generate human-readable insights from analysis.

```python
generate_insights(analysis_results: dict) -> dict
```

**Parameters:**

- `analysis_results` (dict): Results from analyze_trends()

**Returns:**

- `dict`: Insights with scores and summaries

### GoogleTrendsAnalyzer

Google Trends data collection and analysis.

#### Constructor

```python
GoogleTrendsAnalyzer()
```

#### Methods

##### fetch_trending_searches(country='US', limit=20)

Fetch current trending searches.

```python
fetch_trending_searches(country: str = 'US', limit: int = 20) -> list
```

**Parameters:**

- `country` (str): Country code (e.g., 'US', 'GB', 'DE')
- `limit` (int): Maximum number of results

**Returns:**

- `list`: List of trending search topics

##### get_interest_over_time(keyword, timeframe='today 12-m')

Get interest over time for a keyword.

```python
get_interest_over_time(keyword: str, timeframe: str = 'today 12-m') -> dict
```

**Parameters:**

- `keyword` (str): Search keyword
- `timeframe` (str): Time period ('today 12-m', 'today 3-m', etc.)

**Returns:**

- `dict`: Time series interest data

## Rust API

### Crawler Struct

Main crawler structure for Rust implementation.

#### Constructor

```rust
pub fn new(config: CrawlerConfig) -> Self
```

**Parameters:**

- `config`: CrawlerConfig with crawler settings

#### Methods

##### crawl_urls(urls: Vec<String>) -> Result<CrawlResults, CrawlerError>

Crawl multiple URLs.

```rust
pub async fn crawl_urls(&self, urls: Vec<String>) -> Result<CrawlResults, CrawlerError>
```

**Parameters:**

- `urls`: Vector of URLs to crawl

**Returns:**

- `Result<CrawlResults, CrawlerError>`: Crawl results or error

##### crawl_single_url(url: &str) -> Result<PageData, CrawlerError>

Crawl a single URL.

```rust
pub async fn crawl_single_url(&self, url: &str) -> Result<PageData, CrawlerError>
```

**Parameters:**

- `url`: URL to crawl

**Returns:**

- `Result<PageData, CrawlerError>`: Page data or error

### BacklinkProcessor Struct

Backlink discovery and analysis.

#### Constructor

```rust
pub fn new(config: BacklinkConfig) -> Self
```

#### Methods

##### discover_backlinks(target_url: &str) -> Result<Vec<Backlink>, BacklinkError>

Discover backlinks for a target URL.

```rust
pub async fn discover_backlinks(&self, target_url: &str) -> Result<Vec<Backlink>, BacklinkError>
```

##### calculate_pagerank() -> HashMap<String, f64>

Calculate PageRank scores.

```rust
pub fn calculate_pagerank(&self) -> HashMap<String, f64>
```

**Returns:**

- `HashMap<String, f64>`: URL to PageRank score mapping

### Database Module

SQLite database operations.

#### Database Struct

```rust
pub struct Database {
    connection: Connection,
}
```

#### Methods

##### new(path: &str) -> Result<Self, DatabaseError>

Create new database connection.

```rust
pub fn new(path: &str) -> Result<Self, DatabaseError>
```

##### store_page_data(data: &PageData) -> Result<i64, DatabaseError>

Store crawled page data.

```rust
pub fn store_page_data(&self, data: &PageData) -> Result<i64, DatabaseError>
```

##### get_recent_pages(limit: i64) -> Result<Vec<PageData>, DatabaseError>

Get recently crawled pages.

```rust
pub fn get_recent_pages(&self, limit: i64) -> Result<Vec<PageData>, DatabaseError>
```

## Configuration Structures

### Python Configuration

```python
config = {
    # Timing
    'delay': 1.5,                    # Base delay between requests
    'random_delay': True,            # Add random variation
    'delay_range': (1.0, 3.0),       # Random delay range

    # Limits
    'max_depth': 3,                  # Maximum crawl depth
    'max_pages': 100,                # Pages per domain
    'max_total_pages': 1000,         # Total pages

    # Content
    'extract_articles': True,        # Use newspaper3k
    'extract_metadata': True,        # Extract meta tags
    'follow_external': False,        # Stay within domain

    # Performance
    'concurrent_requests': 5,        # Concurrent connections
    'timeout': 30,                   # Request timeout
    'retry_attempts': 3,             # Retry failed requests

    # Output
    'save_to_database': True,        # Store in SQLite
    'export_json': True,             # Export JSON
    'export_csv': False,             # Export CSV

    # Compliance
    'respect_robots': True,          # Honor robots.txt
    'user_agent': 'RatCrawler/1.0',  # User agent string
}
```

### Rust Configuration

```rust
#[derive(Debug, Clone)]
pub struct CrawlerConfig {
    pub user_agent: String,
    pub timeout: Duration,
    pub max_redirects: usize,
    pub max_depth: usize,
    pub max_pages: usize,
    pub delay: Duration,
    pub respect_robots_txt: bool,
    pub concurrent_requests: usize,
    pub retry_attempts: usize,
}

impl Default for CrawlerConfig {
    fn default() -> Self {
        Self {
            user_agent: "RatCrawler/1.0".to_string(),
            timeout: Duration::from_secs(30),
            max_redirects: 5,
            max_depth: 3,
            max_pages: 100,
            delay: Duration::from_millis(1500),
            respect_robots_txt: true,
            concurrent_requests: 5,
            retry_attempts: 3,
        }
    }
}
```

## Error Types

### Python Exceptions

```python
class CrawlerError(Exception):
    """Base crawler exception"""
    pass

class NetworkError(CrawlerError):
    """Network-related errors"""
    pass

class ParseError(CrawlerError):
    """Content parsing errors"""
    pass

class DatabaseError(CrawlerError):
    """Database operation errors"""
    pass

class ConfigurationError(CrawlerError):
    """Configuration-related errors"""
    pass
```

### Rust Error Types

```rust
#[derive(Debug, thiserror::Error)]
pub enum CrawlerError {
    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),

    #[error("Parse error: {0}")]
    Parse(String),

    #[error("Database error: {0}")]
    Database(#[from] rusqlite::Error),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}
```

## Data Structures

### PageData (Python)

```python
@dataclass
class PageData:
    url: str
    title: str
    content: str
    metadata: dict
    status_code: int
    response_time: float
    crawl_date: datetime
    word_count: int
    links: list
    images: list
    videos: list
```

### PageData (Rust)

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PageData {
    pub url: String,
    pub title: String,
    pub content: String,
    pub metadata: HashMap<String, String>,
    pub status_code: u16,
    pub response_time_ms: u64,
    pub crawl_date: DateTime<Utc>,
    pub word_count: usize,
    pub links: Vec<String>,
    pub images: Vec<String>,
    pub videos: Vec<String>,
}
```

### CrawlResults

```python
@dataclass
class CrawlResults:
    successful_crawls: list
    failed_crawls: list
    total_pages: int
    total_size: int
    average_response_time: float
    crawl_duration: float
    start_time: datetime
    end_time: datetime
```

## Examples

### Complete Crawling Workflow

```python
from crawler import EnhancedProductionCrawler
from backlinkprocessor import BacklinkProcessor
from crawlerdb import CrawlerDatabase

# Initialize components
crawler = EnhancedProductionCrawler({
    'delay': 2.0,
    'max_pages': 50,
    'extract_articles': True
})

processor = BacklinkProcessor(delay=1.5, usedatabase=True)
db = CrawlerDatabase('results.db')

# Crawl websites
urls = ['https://example.com', 'https://news-site.com']
results = crawler.comprehensive_crawl(urls)

# Analyze backlinks
processor.crawl_backlinks(urls, max_depth=2)
processor.build_link_graph()
pagerank_scores = processor.calculate_pagerank()

# Store and query results
for page in results['successful_crawls']:
    db.store_crawl_result(page)

# Query results
recent_pages = db.get_recent_crawls(limit=10)
search_results = db.search_content('artificial intelligence')
```

### Trend Analysis Workflow

```python
from trend_analyzer import TrendAnalyzer

# Initialize analyzer
analyzer = TrendAnalyzer()

# Analyze trends
keyword = "artificial intelligence"
results = analyzer.analyze_trends(
    keyword=keyword,
    sources=['google', 'social', 'financial', 'news'],
    time_window='24h'
)

# Generate insights
insights = analyzer.generate_insights(results)

print(f"Trend Score: {insights['trend_score']:.2f}")
print(f"Sentiment: {insights['sentiment']}")
print(f"Peak Activity: {insights['peak_time']}")

# Export analysis
analyzer.export_analysis(results, 'trend_analysis.json')
```

## Best Practices

### Error Handling

```python
# Always handle exceptions
try:
    results = crawler.comprehensive_crawl(urls)
    print(f"Success: {len(results['successful_crawls'])} pages")
except NetworkError as e:
    print(f"Network issue: {e}")
    # Implement retry logic
except DatabaseError as e:
    print(f"Database issue: {e}")
    # Check database connection
except Exception as e:
    print(f"Unexpected error: {e}")
    # Log for debugging
```

### Resource Management

```python
# Use context managers for database connections
with CrawlerDatabase('results.db') as db:
    # Database operations
    results = db.get_recent_crawls(limit=100)

# Clean up resources
crawler.cleanup()
processor.cleanup()
```

### Configuration Validation

```python
# Validate configuration before use
def validate_config(config):
    required_keys = ['delay', 'max_pages', 'user_agent']
    for key in required_keys:
        if key not in config:
            raise ConfigurationError(f"Missing required key: {key}")

    if config['delay'] < 0.1:
        raise ConfigurationError("Delay must be at least 0.1 seconds")

    return True

# Use validated config
if validate_config(config):
    crawler = EnhancedProductionCrawler(config)
```

## Performance Considerations

### Memory Usage

- **Batch Processing**: Process URLs in batches to control memory usage
- **Content Limits**: Set maximum content length to prevent memory issues
- **Cleanup Intervals**: Regularly clean up cached data

### Network Efficiency

- **Connection Pooling**: Reuse connections for better performance
- **Compression**: Enable gzip/deflate compression
- **Concurrent Limits**: Balance concurrency with server capacity

### Database Optimization

- **Indexing**: Create appropriate database indexes
- **Batch Inserts**: Insert multiple records at once
- **Connection Pooling**: Reuse database connections

## Migration Guide

### From v1.x to v2.x

**Breaking Changes:**

- Configuration format has changed
- Database schema updated
- Some method signatures modified

**Migration Steps:**

1. Update configuration dictionaries
2. Run database migration scripts
3. Update method calls to use new signatures
4. Test with small datasets first

### Deprecation Notices

- `old_crawler_method()` is deprecated, use `new_crawler_method()` instead
- SQLite database format will change in v3.0
- Some configuration options will be removed

## Support

- 📖 [Documentation](https://theboringrats.github.io/ratcrawler/)
- 🐛 [Issues](https://github.com/TheBoringRats/ratcrawler/issues)
- 💬 [Discussions](https://github.com/TheBoringRats/ratcrawler/discussions)
- 📧 [Contact](mailto:theboringrats@gmail.com)
