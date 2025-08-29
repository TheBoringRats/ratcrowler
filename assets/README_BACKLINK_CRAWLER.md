# 🕷️ RatCrawler - Backlink Analysis System

A comprehensive backlink crawler and analysis system that discovers, analyzes, and stores website backlink data for SEO and competitive analysis.

## 🚀 Features

- **Web Crawling**: Crawl websites to discover backlink patterns
- **Link Analysis**: Extract and analyze anchor text, context, and link relationships
- **Database Storage**: Store backlinks and analysis results in SQLite database
- **PageRank Calculation**: Calculate PageRank scores for discovered pages
- **Domain Authority**: Calculate domain authority based on backlink profiles
- **Spam Detection**: Identify potentially spammy or low-quality backlinks
- **Graph Visualization**: Create network graphs of link relationships
- **Export Options**: Export results to JSON and CSV formats

## 📋 Requirements

- Python 3.7+
- Required packages: `requests`, `beautifulsoup4`, `networkx`
- Optional: `matplotlib` (for graph visualization)

## 🛠️ Installation

1. **Clone or download the project**

```bash
cd "/home/swadhin/Search engine/ratcrowler"
```

2. **Install dependencies**

```bash
pip install requests beautifulsoup4 networkx
# Optional for visualization:
pip install matplotlib
```

## 🎯 Quick Start

### 1. Test the System

```bash
python3 test_crawler.py
```

### 2. Basic Usage

```python
from backlinkprocessor import BacklinkProcessor

# Initialize processor
processor = BacklinkProcessor(delay=1, usedatabase=True)

# Crawl backlinks
seed_urls = ["https://example.com", "https://another-site.com"]
processor.crawl_backlinks(seed_urls, max_depth=2)

# Build link graph and calculate metrics
processor.build_link_graph()
pagerank_scores = processor.calculate_pagerank()
processor.calculate_domain_authority()

# Detect spam links
spam_links = processor.detect_link_spam()

print(f"Found {len(processor.backlinks)} backlinks")
print(f"Detected {len(spam_links)} spam links")
```

### 3. Production Crawler

```bash
# Basic crawl
python3 production_crawler.py https://example.com https://another-site.com

# Advanced options
python3 production_crawler.py \
    --delay 2.0 \
    --max-depth 3 \
    --export-json \
    --export-csv \
    https://example.com
```

## 📊 Core Components

### 1. BacklinkData Class

Stores individual backlink information:

- Source URL and target URL
- Anchor text and surrounding context
- Page title and metadata
- NoFollow status and domain authority

### 2. BacklinkProcessor Class

Main analysis engine:

- **crawl_backlinks()**: Discover backlinks from seed URLs
- **build_link_graph()**: Create NetworkX graph of relationships
- **calculate_pagerank()**: Compute PageRank scores
- **calculate_domain_authority()**: Calculate domain authority metrics
- **detect_link_spam()**: Identify low-quality links
- **generate_backlink_report()**: Create detailed reports

### 3. BacklinkDatabase Class

Database management:

- **store_backlinks()**: Save backlinks to SQLite database
- **store_domain_scores()**: Save domain authority scores
- **store_pagerank_scores()**: Save PageRank calculations
- **get_backlinks_for_url()**: Retrieve stored backlinks

## 🗄️ Database Schema

The system creates three main tables:

### backlinks

- `source_url`: URL containing the link
- `target_url`: URL being linked to
- `anchor_text`: Link text
- `context`: Surrounding text context
- `page_title`: Title of source page
- `domain_authority`: Domain authority score
- `is_nofollow`: Whether link has nofollow attribute
- `crawl_date`: When link was discovered

### domain_scores

- `domain`: Domain name
- `authority_score`: Calculated authority score (0-100)
- `total_backlinks`: Number of backlinks to domain
- `unique_referring_domains`: Number of unique referring domains

### pagerank_scores

- `url`: Page URL
- `pagerank_score`: Calculated PageRank score
- `last_calculated`: Timestamp of calculation

## 🔧 Configuration Options

### BacklinkProcessor Parameters

- `delay`: Delay between requests (seconds)
- `usedatabase`: Enable/disable database storage

### Crawling Parameters

- `max_depth`: Maximum crawl depth (default: 2)
- `max_pages`: Maximum pages to crawl
- `spam_threshold`: Spam detection threshold (0-1)

### Production Crawler CLI Options

```bash
python3 production_crawler.py [OPTIONS] URL [URL...]

Options:
  --delay FLOAT          Delay between requests (default: 1.5)
  --max-depth INT        Maximum crawl depth (default: 2)
  --spam-threshold FLOAT Spam detection threshold (default: 0.8)
  --no-database         Disable database storage
  --export-json         Export results to JSON
  --export-csv          Export backlinks to CSV
```

## 📈 Analysis Features

### 1. PageRank Calculation

- Uses NetworkX PageRank algorithm
- Considers link weights (nofollow links have reduced weight)
- Helps identify most important pages in the link graph

### 2. Domain Authority

- Calculated based on:
  - Number of unique referring domains
  - Quality of backlinks (dofollow vs nofollow)
  - Anchor text diversity
  - Context richness
- Scale: 0-100

### 3. Spam Detection

Identifies potentially spammy links based on:

- Over-optimized anchor text
- Commercial keywords in anchor text
- Suspicious domain patterns
- Lack of context around links

### 4. Anchor Text Analysis

- Distribution of anchor text across backlinks
- Identification of over-optimization
- Context extraction around links

## 📊 Usage Examples

### Analyze Competitor Backlinks

```python
processor = BacklinkProcessor(delay=2, usedatabase=True)

# Crawl competitor sites
competitor_urls = [
    "https://competitor1.com",
    "https://competitor2.com"
]

processor.crawl_backlinks(competitor_urls, max_depth=2)
processor.calculate_domain_authority()

# Generate reports
for url in competitor_urls:
    report = processor.generate_backlink_report(url)
    print(f"Competitor: {url}")
    print(f"Total backlinks: {report['total_backlinks']}")
    print(f"Domain authority: {report['domain_authority']}")
```

### Export Data for Analysis

```python
# After crawling, export to different formats
processor.export_results("analysis_results.json")

# Get data from database
db = BacklinkDatabase()
backlinks = db.get_backlinks_for_url("https://target-site.com")

# Convert to pandas DataFrame for analysis
import pandas as pd
df = pd.DataFrame(backlinks)
print(df.describe())
```

## ⚠️ Important Notes

### Ethical Crawling

- Always respect robots.txt files
- Use appropriate delays between requests
- Don't overload target servers
- Consider rate limiting for large crawls

### Performance Considerations

- Database grows with each crawl
- Large crawls can take significant time
- Consider using smaller max_depth for initial testing
- Monitor memory usage for very large link graphs

### Legal Considerations

- Ensure compliance with website terms of service
- Respect copyright and data protection laws
- Use for legitimate SEO and research purposes only

## 🐛 Troubleshooting

### Common Issues

1. **Import Error**: Check that all required packages are installed
2. **Database Locked**: Ensure no other processes are using the database
3. **Network Timeouts**: Increase delay parameter for slow websites
4. **Memory Issues**: Reduce max_depth or max_pages for large crawls

### Debug Mode

Enable logging for detailed debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Output Files

The system can generate several output files:

- `backlinks.db`: SQLite database with all data
- `backlink_analysis_[timestamp].json`: Complete analysis results
- `backlinks_[timestamp].csv`: Backlink data in CSV format
- `link_graph.png`: Network visualization (if matplotlib available)

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Add more sophisticated spam detection algorithms
- Implement parallel crawling for better performance
- Add support for JavaScript-rendered pages
- Improve domain authority calculation
- Add more export formats

## 📄 License

See LICENSE file for details.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Run the test script to verify setup
3. Review error messages and logs
4. Consider adjusting configuration parameters

---

**Happy Crawling! 🕷️**
