<div align="center">

# 🕷️ RatCrawler

### **Advanced Web Crawling & Multi-Source Trending Analysis Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.70+-orange.svg)](https://www.rust-lang.org/)
[![SQLAlchemy](https://img.shields.io/badge/Database-SQLAlchemy-red.svg)](https://www.sqlalchemy.org/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-orange.svg)](https://streamlit.io/)

_A comprehensive platform combining intelligent web crawling, backlink analysis, real-time trend monitoring, and social media insights. RatCrawler efficiently navigates the web while analyzing trending topics across Google Trends, Twitter/X, and financial markets._

</div>

---

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Core Features](#-core-features)
- [🏗️ System Architecture](#️-system-architecture)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [🎮 Usage](#-usage)
- [📊 Multi-Source Trend Analysis](#-multi-source-trend-analysis)
- [🔍 Backlink Analysis Engine](#-backlink-analysis-engine)
- [📈 Monitoring & Dashboard](#-monitoring--dashboard)
- [🗄️ Database Schema](#️-database-schema)
- [🧪 Testing](#-testing)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🎯 Overview

**RatCrawler** is a sophisticated **multi-purpose data extraction and analysis platform** that combines:

### 🌟 **Primary Capabilities**

1. **🕷️ Advanced Web Crawler**

   - Intelligent batch processing (50 URLs per batch)
   - Automatic progress tracking and resume functionality
   - Professional backlink discovery and analysis
   - SQLAlchemy-powered multi-database architecture

2. **📈 Multi-Source Trend Analysis**

   - **Google Trends Integration** - Real-time search volume data from 50+ countries
   - **Twitter/X Trends** - Social media trending topics with authentication
   - **Financial Market Analysis** - Stock and crypto trend monitoring
   - **Cross-Platform Correlation** - Identify trending patterns across sources

3. **🔍 Backlink Analysis Engine**

   - PageRank calculation and domain authority scoring
   - Comprehensive link relationship mapping
   - Spam detection and quality assessment
   - Network graph visualization

4. **📊 Real-Time Monitoring**
   - Streamlit-powered dashboard with authentication
   - FastAPI-based monitoring APIs
   - Live progress tracking and analytics
   - System health monitoring

### 🚀 **Dual Implementation**

- **🐍 Python Version** (Primary) - Full-featured with trending analysis
- **🦀 Rust Version** (High-Performance) - Optimized for speed and efficiency

---

## ✨ Core Features

### 🕷️ **Web Crawling Engine**

| Feature                             | Description                                                | Status |
| ----------------------------------- | ---------------------------------------------------------- | ------ |
| **Intelligent Batch Processing**    | Process 50 URLs per batch with automatic progress tracking | ✅     |
| **Auto-Resume Functionality**       | Resume from exactly where you left off after interruption  | ✅     |
| **Professional Backlink Discovery** | Extract and analyze backlink relationships                 | ✅     |
| **Multi-Database Architecture**     | SQLAlchemy with SQLite and Turso cloud support             | ✅     |
| **Async Processing**                | High-performance async/await crawler implementation        | ✅     |
| **Rate Limiting**                   | Respectful crawling with configurable delays               | ✅     |
| **Session Management**              | Comprehensive crawl session tracking                       | ✅     |
| **Error Recovery**                  | Robust error handling with retry mechanisms                | ✅     |

### 📈 **Trending Analysis Suite**

| Platform              | Features                                                  | Implementation           |
| --------------------- | --------------------------------------------------------- | ------------------------ |
| **Google Trends**     | Real-time search volume, 50+ countries, article summaries | `engine/googletrends.py` |
| **Twitter/X Trends**  | Trending topics, authentication support, rate limiting    | `engine/xtrends.py`      |
| **Financial Markets** | Stock trends, crypto monitoring, market analysis          | Integrated               |
| **Cross-Platform**    | Correlation analysis, pattern detection                   | Advanced analytics       |

### 🔍 **Backlink Analysis Engine**

- **🌐 Link Discovery**: Extract backlinks from crawled pages
- **📊 PageRank Calculation**: Google's algorithm implementation
- **🏆 Domain Authority Scoring**: Comprehensive authority metrics
- **🛡️ Spam Detection**: Identify low-quality and spammy links
- **📈 Network Analysis**: Graph-based relationship mapping
- **📋 Comprehensive Reporting**: Detailed backlink analytics

---

## 🏗️ System Architecture

### 🎯 **Platform Overview**

```
RatCrawler Platform
├── 🕷️ Web Crawling Engine
│   ├── Batch Processing (main.py)
│   ├── Progress Tracking (rat/progress.py)
│   ├── Professional Crawler (rat/crawler.py)
│   └── Database Management (rat/sqlalchemy_database.py)
├── 📈 Trending Analysis
│   ├── Google Trends (engine/googletrends.py)
│   ├── Twitter/X Trends (engine/xtrends.py)
│   └── Cross-Platform Analytics
├── 🔍 Backlink Analysis
│   ├── Link Discovery (rat/backlink.py)
│   ├── PageRank Calculation
│   └── Domain Authority Analysis
├── 📊 Monitoring & UI
│   ├── Streamlit Dashboard (dashboard.py)
│   ├── FastAPI Server (rat/log_api.py)
│   └── Authentication System
└── 🗄️ Data Storage
    ├── SQLAlchemy ORM
    ├── SQLite (Local)
    └── Turso (Cloud)
```

### 🔧 **Core Components**

- **Auto Batch Crawler**: Intelligent URL batch processing from backlinks database
- **Professional Crawler**: Advanced async HTTP client with comprehensive content extraction
- **Trending Analysis Engine**: Real-time data from Google Trends and Twitter/X
- **Database Layer**: Multi-database support with automatic schema migration
- **Monitoring Suite**: Real-time dashboard and API monitoring

---

## 🚀 Quick Start

### 🎯 **Choose Your Use Case**

**Web Crawling** (Automatic batch processing)

```bash
git clone https://github.com/TheBoringRats/ratcrowler.git
cd ratcrowler
pip install -r requirements.txt
python main.py  # Starts automatic crawling
```

**Google Trends Analysis**

```bash
cd engine
python googletrends.py --limit 10 --summaries
```

**Twitter/X Trends** (Requires authentication)

```bash
cd engine
python xtrends.py
```

**Backlink Analysis**

```bash
python -c "from rat.backlink import BacklinkDiscoverer; bd = BacklinkDiscoverer(); bd.discover_backlinks(['https://example.com'])"
```

---

## 📦 Installation

### 📋 **Prerequisites**

- **Python 3.8+** (Python 3.13+ recommended)
- **Git** for repository cloning
- **Chrome/Chromium** (for Twitter/X trends)

### 🔧 **Installation Steps**

**1. Clone Repository**

```bash
git clone https://github.com/TheBoringRats/ratcrowler.git
cd ratcrowler
```

**2. Install Dependencies**

```bash
# Standard installation
pip install -r requirements.txt

# With Turso Cloud Database
pip install -r requirements_turso.txt
```

**3. Environment Setup** (Optional)

```bash
# For Twitter/X Integration
cp engine/.env.example engine/.env
# Edit engine/.env with Twitter credentials

# For Turso Cloud Database
cp .env.example .env
# Edit .env with Turso credentials
```

**4. Verification**

```bash
python main.py --help
cd engine && python googletrends.py --limit 1
```

---

## 🎮 Usage

### 🕷️ **Web Crawling**

**Automatic Batch Crawling** (Recommended)

```bash
# Start automatic crawling (no arguments needed)
python main.py

# Check current progress
python main.py --status

# Reset progress and start fresh
python main.py --reset
```

**What happens:**

1. 🔍 Discovers URLs from backlinks database
2. 📦 Processes 50 URLs per batch automatically
3. 💾 Saves progress after each batch
4. 📊 Provides real-time monitoring dashboard
5. 🔄 Resumes exactly where it left off on restart

**Monitoring Interface:**

- **Dashboard**: http://localhost:8501 (starts automatically)
- **API Monitoring**: http://localhost:8000 (logs and metrics)
- **Progress File**: `crawl_progress.json` (detailed progress)

---

## 📊 Multi-Source Trend Analysis

### 🌍 **Google Trends Integration**

**Features:**

- Real-time trending data from 50+ countries
- RSS feed parsing for immediate updates
- Article summary extraction with newspaper3k
- Intelligent rate limiting and retry mechanisms

**Usage:**

```bash
cd engine

# Basic trending topics
python googletrends.py

# Advanced analysis
python googletrends.py --limit 20 --delay 3 --summaries --countries US,GB,DE
```

### 🐦 **Twitter/X Trends**

**Features:**

- Selenium-based trending topic extraction
- Authentication support with cookie persistence
- Real-time social media trend monitoring
- Rate limiting and error recovery

**Setup:**

```bash
cd engine
cp .env.example .env
# Add Twitter credentials to .env
python xtrends.py
```

---

## 🔍 Backlink Analysis Engine

Comprehensive backlink discovery and analysis system for SEO and competitive intelligence.

### **Core Features:**

- **Link Discovery**: Extract backlinks from crawled pages
- **PageRank Calculation**: Google's algorithm implementation
- **Domain Authority**: Comprehensive authority scoring
- **Spam Detection**: Identify low-quality links
- **Network Analysis**: Graph-based relationship mapping

### **Usage Examples:**

**Basic Backlink Discovery:**

```python
from rat.backlink import BacklinkDiscoverer

discoverer = BacklinkDiscoverer()
backlinks = discoverer.discover_backlinks(['https://example.com'])
print(f"Found {len(backlinks)} backlinks")
```

**Domain Authority Analysis:**

```python
authority = discoverer.calculate_domain_authority('example.com')
print(f"Domain Authority Score: {authority}")
```

---

## 📈 Monitoring & Dashboard

### 🎛️ **Real-Time Dashboard**

Access the Streamlit dashboard at: http://localhost:8501

**Features:**

- Live crawl progress tracking
- Performance metrics and analytics
- System health monitoring
- Database status overview
- Session management interface

### 🌐 **API Monitoring**

FastAPI server at: http://localhost:8000

**Key Endpoints:**

- `GET /health` - System health status
- `GET /logs` - Recent crawl logs
- `GET /stats` - Performance statistics
- `GET /progress` - Current crawl progress

---

## 🗄️ Database Schema

RatCrawler uses SQLAlchemy with support for both SQLite (local) and Turso (cloud) databases.

### **Core Tables:**

**Crawled Pages:**

```sql
CREATE TABLE crawled_pages (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content TEXT,
    word_count INTEGER,
    http_status_code INTEGER,
    crawl_timestamp DATETIME,
    session_id TEXT,
    content_hash TEXT
);
```

**Backlinks:**

```sql
CREATE TABLE backlinks (
    id INTEGER PRIMARY KEY,
    source_url TEXT NOT NULL,
    target_url TEXT NOT NULL,
    anchor_text TEXT,
    discovered_timestamp DATETIME,
    domain_authority_score REAL
);
```

---

## 🧪 Testing

Comprehensive test suite for reliability and performance validation.

**Run Tests:**

```bash
# All tests
pytest tests/ -v

# Specific components
pytest tests/test_crawler.py -v
pytest tests/test_trends.py -v

# With coverage
pytest --cov=rat tests/
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

**Development Setup:**

```bash
git clone https://github.com/TheBoringRats/ratcrowler.git
cd ratcrowler
pip install -r requirements.txt
pytest tests/  # Ensure tests pass
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Trends API** for trend data
- **SQLAlchemy** for database management
- **Streamlit** for dashboard framework
- **FastAPI** for monitoring APIs
- **BeautifulSoup** for HTML parsing
- **aiohttp** for async HTTP processing

---

<div align="center">

## 🚀 **Get Started Today**

```bash
git clone https://github.com/TheBoringRats/ratcrowler.git
cd ratcrowler
pip install -r requirements.txt
python main.py
```

**⭐ Star us on GitHub | 🐛 Report Issues | 💡 Request Features**

---

**Built with ❤️ by [TheBoringRats](https://github.com/TheBoringRats)**

_Intelligent web crawling and trend analysis for the modern web_

</div>
