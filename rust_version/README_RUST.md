# RatCrawler Rust Version

A high-performance, scheduled web crawler and backlink analyzer built in Rust with real-time dashboard monitoring.

## Features

🚀 **Intelligent Scheduling**: Automatically switches between crawling and backlink processing based on time-of-day schedule
🔗 **Advanced Backlink Discovery**: Finds and analyzes backlinks with context and anchor text extraction
📊 **Real-time Dashboard**: Beautiful web interface with live statistics and system monitoring
🎯 **Smart URL Management**: Automatically discovers and adds unique domains to the seed URL database
⚡ **High Performance**: Built in Rust for maximum speed and concurrent processing
📈 **Progress Tracking**: Comprehensive metrics and analytics

## Architecture

The system operates in two main modes:

### 1. Backlink Processing Mode (2 hours, 4 times per day)

- **Default Schedule**: 2 AM, 8 AM, 2 PM, 8 PM (configurable)
- Discovers backlinks from seed URLs
- Extracts anchor text, context, and page metadata
- Automatically adds unique domains to seed database
- Analyzes domain authority and link relationships

### 2. Crawling Mode (Remaining time)

- Crawls web pages from seed URLs
- Extracts comprehensive page data (title, content, meta tags, etc.)
- Discovers new URLs for future crawling
- Updates seed URLs with unique domains found

## Installation & Setup

### Prerequisites

- Rust 1.70 or later
- SQLite 3

### Build Instructions

```bash
# Clone the repository
cd rust_version

# Build the project
cargo build --release

# Run the crawler
cargo run --release
```

### Configuration

The system uses default configurations that can be customized:

- **Backlink Processing Hours**: Default: [2, 8, 14, 20] (4 times per day, 2 hours each)
- **Crawling Parameters**: Concurrent requests, delays, timeouts
- **Database**: SQLite with automatic schema creation
- **Dashboard Port**: Default: 8080

## Usage

### Starting the System

```bash
cargo run --release
```

This will:

1. Initialize the SQLite database
2. Load seed URLs from `seed_urls.json`
3. Start the scheduler
4. Launch the web dashboard on http://localhost:8080
5. Begin automated crawling/backlink processing

### Dashboard Access

Open your browser to `http://localhost:8080` to view:

- **Real-time Statistics**: URLs crawled, backlinks found, system performance
- **Current Mode**: Shows whether system is crawling or processing backlinks
- **Recent Activity**: Latest crawled pages
- **System Health**: Memory usage, CPU usage, database size
- **Progress Tracking**: Rates per hour, efficiency metrics

### Seed URL Management

The system automatically:

- Loads initial seed URLs from `seed_urls.json`
- Discovers new unique domains during crawling
- Adds high-quality URLs to the seed database
- Prioritizes URLs based on crawl success and domain authority

## Database Schema

The system creates several tables:

- **`crawl_results`**: Comprehensive page data from crawling
- **`backlinks`**: Discovered backlink relationships
- **`seed_urls`**: Managed list of URLs to crawl
- **`stats`**: Dashboard statistics and metrics

## API Endpoints

The dashboard server provides REST endpoints:

- `GET /` - Main dashboard interface
- `GET /api/stats` - Current system statistics
- `GET /api/recent-crawls` - Recent crawl results
- `GET /health` - System health check

## Performance Tuning

### Concurrent Requests

```rust
CrawlerConfig {
    max_concurrent_requests: 10, // Adjust based on your system
    delay_between_requests_ms: 1000, // Be respectful to target servers
    request_timeout_seconds: 30,
    // ...
}
```

### Schedule Customization

```rust
ScheduleConfig {
    backlink_hours: vec![2, 8, 14, 20], // When to process backlinks
    crawling_hours: vec![/* remaining hours */], // When to crawl
    timezone: "UTC".to_string(),
}
```

## Monitoring & Logging

The system provides comprehensive logging:

- Info level: Mode switches, completion statistics
- Warn level: Missing seed URLs, failed requests
- Error level: Database errors, system failures

Dashboard metrics include:

- URLs crawled per hour
- Backlinks discovered per hour
- System resource usage
- Database size growth

## Comparison with Python Version

This Rust implementation offers several advantages over the Python version:

- **Performance**: 5-10x faster crawling speeds
- **Memory Efficiency**: Lower memory footprint
- **Concurrency**: Better handling of concurrent requests
- **Reliability**: Strong type system prevents runtime errors
- **Scheduling**: Built-in intelligent time-based scheduling
- **Dashboard**: Modern, real-time web interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
