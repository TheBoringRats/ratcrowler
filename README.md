<div align="center">

# 🕷️ RatCrawler

---

**A comprehensive web crawler and multi-source trending analysis system**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.70+-orange.svg)](https://www.rust-lang.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-green.svg)](https://www.sqlite.org/)

---

\_Inspired by the silent and agile nature of a rat, RatCrawler navigates the-------

## 🗄️ Database Schema 🗄️ Database Schema

### Python Database (`website_crawler.db`) 🗄️ Database Schema️ Database Schema

### Python Database (`website_crawler.db`)ternet efficiently, indexing, scraping, and analyzing content across millions of pages. Our comprehensive trending a## 🔍 Google Trends Integrationalysis system aggregates data from Google Trends, social media platforms, financial markets, and emerging news sources to provide real-time insights into trending topics and market movements.\_

</div>

---

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [🚀 Quick Start](#-quick-start)
- [🔧 Installation](#-installation)
- [📊 Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [📈 Performance Comparison](#-performance-comparison)
- [🎮 Usage](#-usage)
- [🔍 Comprehensive Trending Analysis](#-comprehensive-trending-analysis)
- [📊 Google Trends Integration](#-google-trends-integration)
- [📱 Social Media Trends](#-social-media-trends)
- [💰 Financial Market Analysis](#-financial-market-analysis)
- [📰 News & Emerging Trends](#-news--emerging-trends)
- [🗄️ Database Schema](#️-database-schema)
- [⚙️ Configuration](#️-configuration)
- [🧪 Testing](#-testing)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)

---

## 🎯 Overview

RatCrawler is a comprehensive web crawling and **multi-source trending analysis system** available in **two high-performance implementations**:

### 🐍 **Python Version** (Primary)

- **Enhanced Production Crawler** with scheduled automation
- **Backlink Analysis Engine** with PageRank and domain authority
- **Comprehensive Trending Analysis** across multiple platforms
- **Google Trends Integration** for search volume analysis
- **Social Media Trends** from Twitter, Reddit, and more
- **Financial Market Analysis** for stock and crypto trends
- **News & Emerging Trends** from major news sources
- **SQLite Database** with optimized schema
- **Scheduled Crawling** with configurable automation

### 🦀 **Rust Version** (High-Performance)

- **Async/Await** concurrency with tokio runtime
- **Memory-Safe** with zero-cost abstractions
- **Lightning-Fast** compiled performance
- **Multi-Source Data Aggregation** with parallel processing
- **Real-time Trend Analysis** with streaming data
- **Minimal Dependencies** with Rust's rich ecosystem

---

## 🚀 Quick Start

### Python Version (Recommended for beginners)

```bash
# Install dependencies
pip install requests beautifulsoup4 networkx schedule feedparser newspaper3k lxml_html_clean

# Quick test crawl
cd /home/swadhin/Search\ engine/ratcrowler
python3 main.py
```

### Rust Version (Recommended for production)

```bash
# Build and run
cd rust_version
cargo build --release
./target/release/rat-crawler crawl https://example.com
```

### Google Trends Analysis

```bash
# Fetch trending topics
cd engine
python3 googletrends.py --limit 5 --delay 3 --summaries
```

---

## 🔧 Installation

### Prerequisites

#### For Python Version

```bash
# Required packages
pip install requests beautifulsoup4 networkx schedule feedparser newspaper3k lxml_html_clean

# Optional for enhanced features
pip install pandas matplotlib seaborn
```

#### For Rust Version

```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libsqlite3-dev pkg-config

# Install system dependencies (macOS)
brew install sqlite3
```

### Full Installation

```bash
# Clone and setup
git clone https://github.com/TheBoringRats/ratcrowler.git
cd ratcrawler

# Python setup
pip install -r requirements.txt

# Rust setup
cd rust_version
cargo build --release
```

---

## 📊 Features

### 🌟 Core Features

| Feature                   | Python | Rust | Description                              |
| ------------------------- | ------ | ---- | ---------------------------------------- |
| **Web Crawling**          | ✅     | ✅   | Recursive website content extraction     |
| **Backlink Analysis**     | ✅     | ✅   | Discover and analyze backlinks           |
| **PageRank Calculation**  | ✅     | ✅   | Google's algorithm implementation        |
| **Domain Authority**      | ✅     | ✅   | Domain scoring and ranking               |
| **Multi-Source Trends**   | ✅     | ✅   | Google, Social, Financial, News analysis |
| **Real-time Monitoring**  | ✅     | ✅   | 24-hour trend tracking                   |
| **Sentiment Analysis**    | ✅     | ✅   | Advanced sentiment and correlation       |
| **Robots.txt Compliance** | ✅     | ✅   | Respects website policies                |
| **Duplicate Detection**   | ✅     | ✅   | Content hashing and deduplication        |
| **Spam Detection**        | ✅     | ✅   | Advanced spam link identification        |
| **Database Storage**      | ✅     | ✅   | SQLite with optimized schema             |
| **Data Export**           | ✅     | ✅   | JSON/CSV export capabilities             |

### 🚀 Advanced Features

#### Python Exclusive

- **Scheduled Crawling** - Automated daily/weekly crawling
- **Multi-Source Trend Integration** - Comprehensive trend analysis
- **Advanced Reporting** - Multi-platform insights and correlations
- **Dynamic Configuration** - Runtime parameter adjustment
- **Rich Analytics Dashboard** - Visual trend analysis

#### Rust Exclusive

- **Async Concurrency** - Non-blocking I/O operations
- **Memory Safety** - Zero-cost abstractions and guarantees
- **Compiled Performance** - Native machine code execution
- **Parallel Trend Processing** - Multi-source data aggregation
- **High-Throughput Analytics** - Real-time trend processing

---

## 🏗️ Architecture

### Python Architecture

```text
ratcrawler/
├── 🏠 main.py                 # Main scheduled crawler script
├── 🕷️ crawler.py              # EnhancedProductionCrawler class
├── 🔗 backlinkprocessor.py    # Backlink analysis engine
├── 🗄️ crawlerdb.py            # Database management for crawled content
├── 🔗 backlinkdb.py           # Database management for backlinks
├── 🔄 integrated_backlink_crawler.py  # Combined crawler
├── 📊 trend_analyzer.py       # Multi-source trend analysis engine
├── 🌱 seed_urls.json          # Seed URLs for crawling
├── ⚙️ config.py               # Configuration settings
├── 🧪 test_*.py               # Test files
└── 📊 engine/
    ├── 📈 googletrends.py     # Google Trends scraper
    ├── 📱 social_trends.py    # Social media trend analysis
    ├── 💰 financial_trends.py # Financial market analysis
    ├── 📰 news_trends.py      # News and emerging trends
    ├── 📊 trends.json         # Trends data storage
    └── 🔄 correlation_engine.py # Cross-platform correlation analysis
```

### Rust Architecture

```text
rust_version/
├── 🏠 src/main.rs              # CLI entry point
├── 📚 src/lib.rs               # Library exports
├── 🏗️ src/models.rs            # Data structures
├── 🗄️ src/database.rs          # SQLite database operations
├── 🕷️ src/crawler.rs           # Web crawling logic
├── 🔗 src/backlink_processor.rs # Backlink discovery
├── � src/trend_analyzer.rs    # Multi-source trend analysis
├── �🔄 src/integrated_crawler.rs # Combined functionality
├── 📈 src/google_trends.rs     # Google Trends integration
├── 📱 src/social_trends.rs     # Social media analysis
├── 💰 src/financial_trends.rs  # Financial market analysis
└── 📰 src/news_trends.rs       # News and emerging trends
```

---

## 📈 Performance Comparison

| Metric           | Python Version | Rust Version | Improvement      |
| ---------------- | -------------- | ------------ | ---------------- |
| **Memory Usage** | ~150MB         | ~25MB        | **5.6x less**    |
| **Request/sec**  | ~50            | ~500         | **10x faster**   |
| **Startup Time** | ~2s            | ~0.1s        | **20x faster**   |
| **CPU Usage**    | High           | Low          | **3x efficient** |
| **Concurrency**  | Threading      | Async/Await  | **Superior**     |
| **Type Safety**  | Dynamic        | Static       | **Guaranteed**   |

---

## 🎮 Usage

### Python Version

#### Basic Crawling

```bash
# Single website crawl
python3 -c "
from crawler import EnhancedProductionCrawler
crawler = EnhancedProductionCrawler({'delay': 1.5, 'max_depth': 3})
results = crawler.comprehensive_crawl(['https://example.com'])
crawler.print_summary(results)
"
```

#### Scheduled Crawling

```bash
# Automated daily crawling
python3 main.py
```

#### Backlink Analysis

```python
from backlinkprocessor import BacklinkProcessor

processor = BacklinkProcessor(delay=1.0, usedatabase=True)
processor.crawl_backlinks(['https://example.com'], max_depth=2)
processor.build_link_graph()
pagerank_scores = processor.calculate_pagerank()
```

### Rust Version

#### Basic Commands

```bash
# Web crawling
./target/release/rat-crawler crawl https://example.com

# Backlink analysis
./target/release/rat-crawler backlinks https://example.com/page

# Integrated analysis
./target/release/rat-crawler integrated https://example.com

# Domain analysis
./target/release/rat-crawler domain example.com
```

#### Advanced Usage

```bash
# Multiple URLs with custom settings
./target/release/rat-crawler crawl \
  --url https://example.com \
  --url https://example.org \
  --max-pages 500 \
  --respect-robots-txt
```

---

## � Weekly Crawling Workflow

RatCrawler implements a sophisticated **7-day automated workflow** that systematically crawls websites, extracts backlinks, and analyzes domain authority. The system automatically discovers new domains and expands the crawl frontier.

### 🗓️ Weekly Schedule

| Day           | Time        | Activity                   | Description                                               |
| ------------- | ----------- | -------------------------- | --------------------------------------------------------- |
| **Monday**    | 08:00       | 🔗 **Backlink Extraction** | Crawl all seed URLs, extract backlinks, store in database |
| **Tuesday**   | 08:00       | 🌐 **Seed Domain Crawl**   | Deep crawl of all pages within seed domains               |
| **Wednesday** | 08:00       | 🏗️ **Subdomain Analysis**  | Crawl discovered subdomains and analyze content           |
| **Thursday**  | 08:00       | 🏗️ **Subdomain Analysis**  | Continue subdomain crawling (extended session)            |
| **Friday**    | 08:00       | 📥 **Data Retrieval**      | Extract and save backlink data for analysis               |
| **Saturday**  | 08:00       | 📥 **Data Retrieval**      | Additional backlink data extraction                       |
| **Sunday**    | 08:00       | 📊 **System Status**       | Generate reports and system health check                  |
| **Daily**     | 00:00-02:00 | ⚙️ **Engine Services**     | 2-hour maintenance window for data processing             |

### 🔄 Workflow Details

#### Day 1: Backlink Extraction (Monday)

```python
# Configuration for backlink-focused crawling
backlink_config = {
    'max_depth': 1,          # Shallow crawl for backlinks
    'max_pages': 50,         # Limited pages per domain
    'analyze_backlinks': True,
    'stay_on_domain': False  # Allow external link discovery
}

# Extract backlinks from all seed URLs
results = crawler.comprehensive_crawl(seed_urls)
```

**Key Activities:**

- Visit all URLs in `seed_urls.json`
- Extract outbound links (backlinks for other sites)
- Store backlinks in database with metadata
- Calculate initial domain authority scores
- **Auto-Discovery**: Identify high-authority domains (score > 50)
- **Auto-Expansion**: Add valuable domains to `seed_urls.json`

#### Day 2: Seed Domain Deep Crawl (Tuesday)

```python
# Configuration for comprehensive domain coverage
domain_config = {
    'max_depth': 4,          # Deeper exploration
    'max_pages': 200,        # More pages per domain
    'stay_on_domain': True,  # Stay within seed domains
    'analyze_backlinks': False
}
```

**Key Activities:**

- Crawl all pages within seed domains
- Extract comprehensive content and metadata
- Build internal link graphs
- Identify subdomains for further analysis

#### Days 3-4: Subdomain Analysis (Wednesday-Thursday)

```python
# Configuration for subdomain exploration
subdomain_config = {
    'max_depth': 3,
    'max_pages': 150,
    'stay_on_domain': False,
    'analyze_backlinks': True
}

# Get discovered subdomains from database
subdomains = crawler.database.get_discovered_subdomains()
```

**Key Activities:**

- Analyze previously discovered subdomains
- Crawl subdomain content and extract backlinks
- Update domain authority scores
- Identify additional crawl targets

#### Daily Engine Services (00:00-02:00)

```python
# 2-hour automated maintenance window
def run_daily_engine_services():
    # Update domain authority scores
    domain_scores = crawler.database.get_domain_authority_scores()

    # Recalculate PageRank scores
    pagerank_scores = crawler.database.get_pagerank_scores()

    # Clean up old data (keep last 30 days)
    cleanup_count = crawler.database.cleanup_old_data(days_old=30)

    # Analyze recent backlinks
    recent_backlinks = crawler.database.get_recent_backlinks(hours=24)
```

**Key Activities:**

- **Domain Authority Updates**: Recalculate domain scores
- **PageRank Recalculation**: Update page importance scores
- **Data Cleanup**: Remove old records while preserving recent data
- **Backlink Analysis**: Process new backlinks from recent crawls
- **System Optimization**: Database maintenance and performance tuning

### 🎯 Smart Domain Discovery

```python
def add_necessary_domains_to_seeds(crawler, threshold_score=50):
    """Add high-authority domains to seed URLs"""
    domain_scores = crawler.database.get_domain_authority_scores()

    for domain, score in domain_scores.items():
        if score >= threshold_score and domain not in current_seeds:
            # Add to seed_urls.json
            new_url = f"https://{domain}"
            seed_urls.append(new_url)
```

**Discovery Criteria:**

- Domain Authority Score > 50
- Not already in seed URLs
- Successful previous crawls
- Quality backlink profile

### 📊 Monitoring & Reporting

#### System Status (Sunday)

```python
def show_system_status():
    all_backlinks = crawler.get_all_backlinks()
    crawled_urls = crawler.database.get_all_crawled_urls()

    print(f"Total pages crawled: {len(crawled_urls)}")
    print(f"Total backlinks: {len(all_backlinks)}")
    print(f"Database size: {os.path.getsize('website_crawler.db')} bytes")
```

#### Real-time Monitoring

- **Database Health**: Connection status and performance
- **Crawl Progress**: Pages processed, errors encountered
- **Backlink Growth**: New backlinks discovered daily
- **Domain Expansion**: New domains added to seed list

### 🚀 Running the Workflow

#### Automated Mode (Recommended)

```bash
# Start the automated weekly crawler
python3 main.py
```

#### Manual Testing

```bash
# Test individual components
python3 test_workflow.py

# Run specific day functions
python3 -c "from main import perform_backlink_extraction; perform_backlink_extraction()"
```

#### Configuration

```python
# Customize workflow in main.py
config = {
    'delay': 1.5,              # Request delay (seconds)
    'max_depth': 3,            # Crawl depth
    'max_pages': 100,          # Pages per session
    'db_path': 'website_crawler.db',
    'domain_threshold': 50,    # Minimum authority for auto-addition
    'analyze_backlinks': True,
    'stay_on_domain': True
}
```

### 📈 Benefits of This Workflow

1. **Systematic Coverage**: Ensures comprehensive crawling of seed domains
2. **Smart Discovery**: Automatically finds valuable new domains
3. **Resource Management**: Distributes crawling load across the week
4. **Data Freshness**: Regular updates while avoiding duplicate work
5. **Scalability**: Easy to add new domains and adjust crawl parameters
6. **Maintenance**: Automated cleanup and optimization
7. **Monitoring**: Regular health checks and reporting

### 🔧 Customization

#### Adjusting the Schedule

```python
# Modify schedule in main.py
schedule.every().monday.at("09:00").do(perform_backlink_extraction)  # Change time
schedule.every(2).days.do(perform_subdomain_crawl)  # Change frequency
```

#### Modifying Discovery Criteria

```python
# Adjust domain addition threshold
add_necessary_domains_to_seeds(crawler, threshold_score=75)  # Higher bar
```

#### Custom Engine Services

```python
# Add custom maintenance tasks
def custom_engine_task():
    # Your custom processing logic
    pass

# Add to daily services
schedule.every().day.at("01:00").do(custom_engine_task)
```

---

## 🔍 Google Trends Integration

### Features

- **50+ Countries** supported
- **Real-time Trends** from Google Trends RSS
- **Article Summaries** with intelligent extraction
- **Rate Limiting** protection
- **JSON Export** with structured data

### Usage

```bash
# Basic trends fetch
cd engine
python3 googletrends.py

# Advanced configuration
python3 googletrends.py
  --limit 10
  --delay 5
  --summaries
  --output custom_trends.json
  --max-retries 3
```

### Sample Output

```json
{
  "United States": [
    {
      "trend_title": "breaking news",
      "approx_traffic": "1M+",
      "published": "2025-08-29T12:00:00Z",
      "news_items": [
        {
          "title": "News Article Title",
          "url": "https://news.example.com/article",
          "source": "News Source"
        }
      ],
      "summary": "Article summary extracted from content..."
    }
  ]
}
```

---

## 🗄️ Database Schema

## �🔍 Google Trends Integration

### Features

- **50+ Countries** supported
- **Real-time Trends** from Google Trends RSS
- **Article Summaries** with intelligent extraction
- **Rate Limiting** protection
- **JSON Export** with structured data

### Usage

```bash
# Basic trends fetch
cd engine
python3 googletrends.py

# Advanced configuration
python3 googletrends.py \
  --limit 10 \
  --delay 5 \
  --summaries \
  --output custom_trends.json \
  --max-retries 3
```

### Sample Output

```json
{
  "United States": [
    {
      "trend_title": "breaking news",
      "approx_traffic": "1M+",
      "published": "2025-08-29T12:00:00Z",
      "news_items": [
        {
          "title": "News Article Title",
          "url": "https://news.example.com/article",
          "source": "News Source"
        }
      ],
      "summary": "Article summary extracted from content..."
    }
  ]
}
```

---

## 🗄️ Database Schema

### Python Database (`website_crawler.db`)

```sql
-- Crawled content
crawled_pages (
    id, url, title, content, meta_description,
    word_count, response_time_ms, crawl_date
)

-- Backlinks data
backlinks (
    id, source_url, target_url, anchor_text,
    context, page_title, domain_authority, is_nofollow
)

-- Analysis results
domain_scores (domain, authority_score, total_backlinks)
pagerank_scores (url, pagerank_score)
```

### Rust Database (`web_crawl.db`)

```sql
-- Similar schema optimized for Rust
crawl_sessions, crawled_pages, crawl_errors
backlinks, domain_scores, pagerank_scores
```

---

## ⚙️ Configuration

### Python Configuration

```python
config = {
    'delay': 1.5,           # Seconds between requests
    'max_depth': 3,         # Maximum crawl depth
    'max_pages': 100,       # Pages per session
    'user_agent': 'Custom-Agent/1.0',
    'db_path': 'crawler.db', # Database file
    'export_json': True,    # Enable JSON export
    'export_csv': False,    # Enable CSV export
    'analyze_backlinks': True,  # Enable backlink analysis
    'recrawl_days': 7       # Days before recrawling
}
```

### Rust Configuration

```rust
let config = CrawlerConfig {
    user_agent: "RatCrawler/1.0".to_string(),
    timeout: Duration::from_secs(10),
    max_redirects: 5,
    max_depth: 3,
    max_pages: 100,
    delay: Duration::from_millis(1500),
    respect_robots_txt: true,
};
```

---

## 🧪 Testing

### Python Tests

```bash
# Run all tests
python3 -m pytest test_*.py -v

# Run specific test
python3 test_crawler.py

# Quick component test
python3 test_quick.py
```

### Rust Tests

```bash
# Run all tests
cargo test

# Run with verbose output
cargo test -- --nocapture

# Run specific test
cargo test test_crawler
```

### Integration Tests

```bash
# Test full crawling pipeline
python3 -c "
from crawler import EnhancedProductionCrawler
crawler = EnhancedProductionCrawler({'max_pages': 5})
results = crawler.comprehensive_crawl(['https://httpbin.org'])
print(f'Success: {results.get(\"success\")}')
"
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. **Fork the repository**
2. **Clone your fork**

   ```bash
   git clone https://github.com/yourusername/ratcrawler.git
   cd ratcrawler
   ```

3. **Create a feature branch**

   ```bash
   git checkout -b feature/amazing-feature
   ```

4. **Make your changes**
5. **Run tests**

   ```bash
   # Python
   python3 -m pytest

   # Rust
   cargo test
   ```

6. **Submit a pull request**

### Code Style

- **Python**: Follow PEP 8, use type hints
- **Rust**: Use `cargo fmt` and `cargo clippy`
- **Documentation**: Update README for new features

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```text
MIT License

Copyright (c) 2025 TheBoringRats

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🙏 Acknowledgments

### Core Team

- **TheBoringRats** - Project maintainers and core developers
- **swadhinbiswas** - Core developer and contributor

### Technologies Used

- **Python** - Primary implementation language
- **Rust** - High-performance implementation
- **SQLite** - Database engine
- **Tokio** - Async runtime for Rust
- **BeautifulSoup4** - HTML parsing for Python
- **Scraper** - HTML parsing for Rust

### Inspiration

- Inspired by the need for efficient, stealth web crawling
- Built for researchers, SEO analysts, and developers
- Thanks to the open-source community for amazing tools

### Special Thanks

- **Rust Community** - For excellent documentation and crates
- **Python Community** - For rich ecosystem and libraries
- **Contributors** - For their valuable contributions

---

<div align="center">

**Made with ❤️ by TheBoringRats**

[🐛 Report Bug](https://github.com/TheBoringRats/ratcrawler/issues) • [💡 Request Feature](https://github.com/TheBoringRats/ratcrawler/issues) • [📧 Contact](mailto:theboringrats@gmail.com)

---

_⭐ Star us on GitHub if you find this project useful!_

</div>
