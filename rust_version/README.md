# Rat Crawler - Rust Edition

A high-performance web crawler and backlink analyzer written in Rust. This is a complete rewrite of the Python crawler in Rust, offering better performance, memory safety, and concurrency.

## Features

- 🚀 **High Performance**: Written in Rust for maximum speed and memory efficiency
- 🕷️ **Advanced Web Crawling**: Respects robots.txt, handles redirects, extracts structured data
- 🔗 **Backlink Analysis**: Discover and analyze backlinks from search engines and web pages
- 📊 **Comprehensive Analytics**: Domain authority scoring, PageRank calculation, spam detection
- 🗄️ **SQLite Storage**: Efficient local database storage for crawled data and backlinks
- ⚡ **Async/Await**: Concurrent crawling with tokio runtime
- 🔧 **Configurable**: Highly customizable crawling parameters and timeouts

## Installation

### Prerequisites

- Rust 1.70+ (install from [rustup.rs](https://rustup.rs/))
- SQLite3 development libraries

### Build from Source

```bash
# Clone the repository
cd /home/swadhin/Search\ engine/ratcrowler/rust_version

# Build the project
cargo build --release

# Run the crawler
./target/release/rat-crawler --help
```

## Usage

### Basic Web Crawling

```bash
# Crawl a single website
./target/release/rat-crawler crawl https://example.com

# Crawl multiple websites
./target/release/rat-crawler crawl https://example.com https://example.org
```

### Backlink Analysis

```bash
# Analyze backlinks for a specific page
./target/release/rat-crawler backlinks https://example.com/page

# Analyze backlinks for multiple pages
./target/release/rat-crawler backlinks https://example.com/page1 https://example.com/page2
```

### Integrated Crawling

```bash
# Crawl website and analyze backlinks together
./target/release/rat-crawler integrated https://example.com
```

### Domain Analysis

```bash
# Comprehensive domain analysis
./target/release/rat-crawler domain example.com
```

## Configuration

The crawler can be configured through code when creating instances. Key configuration options include:

- **User Agent**: Custom user agent string
- **Timeout**: Request timeout in seconds
- **Max Redirects**: Maximum number of redirects to follow
- **Max Depth**: Maximum crawling depth
- **Max Pages**: Maximum pages to crawl per session
- **Delay**: Delay between requests in milliseconds
- **Robots.txt**: Whether to respect robots.txt files

## Database Schema

### Web Crawl Database (`web_crawl.db`)

- `crawl_sessions`: Crawl session metadata
- `crawled_pages`: Detailed page information and content
- `crawl_errors`: Error logging and tracking

### Backlink Database (`backlinks.db`)

- `backlinks`: Backlink data with anchor text and context
- `domain_scores`: Domain authority scores
- `pagerank_scores`: PageRank calculations

## Architecture

```
ratcrawler/
├── src/
│   ├── main.rs           # CLI entry point
│   ├── lib.rs            # Library exports
│   ├── models.rs         # Data structures
│   ├── database.rs       # SQLite database operations
│   ├── crawler.rs        # Web crawling logic
│   ├── backlink_processor.rs  # Backlink discovery
│   └── integrated_crawler.rs  # Combined functionality
├── Cargo.toml           # Dependencies
└── README.md           # This file
```

## Key Components

### WebsiteCrawler

- Handles web page crawling with robots.txt compliance
- Extracts structured data (title, meta tags, content, links)
- Implements priority queue for efficient crawling
- Supports configurable depth and page limits

### BacklinkProcessor

- Discovers backlinks from search engines (Google, Bing)
- Analyzes page content for backlink opportunities
- Calculates domain authority scores
- Detects spam backlinks using heuristics

### IntegratedCrawler

- Combines web crawling and backlink analysis
- Provides comprehensive domain analysis
- Includes scheduling capabilities
- Generates detailed reports

## Performance Features

- **Async I/O**: Non-blocking HTTP requests with tokio
- **Concurrent Processing**: Multiple pages crawled simultaneously
- **Memory Efficient**: Streaming response processing
- **Smart Caching**: robots.txt and content hash caching
- **Timeout Handling**: Prevents hanging on slow responses

## Error Handling

The crawler includes comprehensive error handling for:

- Network timeouts and connection errors
- HTTP error status codes
- Invalid URLs and parsing errors
- Database connection issues
- Robots.txt parsing problems

## Comparison with Python Version

| Feature      | Python Version | Rust Version |
| ------------ | -------------- | ------------ |
| Performance  | Good           | Excellent    |
| Memory Usage | High           | Low          |
| Concurrency  | Threading      | Async/Await  |
| Type Safety  | Dynamic        | Static       |
| Compilation  | Interpreted    | Compiled     |
| Dependencies | Many           | Minimal      |

## Development

### Running Tests

```bash
cargo test
```

### Code Formatting

```bash
cargo fmt
```

### Linting

```bash
cargo clippy
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run `cargo test` and `cargo clippy`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Rust's excellent ecosystem
- Inspired by the original Python implementation
- Thanks to the open-source community for amazing crates
