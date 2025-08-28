---
layout: default
title: Installation
nav_order: 2
parent: Getting Started
description: "Complete installation guide for RatCrawler"
---

# Installation Guide

This guide will help you install and set up RatCrawler on your system.

## Prerequisites

### System Requirements

- **Python Version**: 3.8 or higher
- **Rust Version**: 1.70 or higher (for Rust implementation)
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 500MB free space

### Required Software

- **Python 3.8+** with pip
- **Rust** (optional, for high-performance version)
- **Git** for cloning the repository

## Quick Installation

### Option 1: Python Version (Recommended)

```bash
# Clone the repository
git clone https://github.com/TheBoringRats/ratcrawler.git
cd ratcrawler

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "from crawler import EnhancedProductionCrawler; print('Installation successful!')"
```

### Option 2: Rust Version (High-Performance)

```bash
# Clone the repository
git clone https://github.com/TheBoringRats/ratcrawler.git
cd ratcrawler/rust_version

# Build the Rust version
cargo build --release

# Verify installation
./target/release/rat-crawler --help
```

### Option 3: Docker Installation

```bash
# Clone the repository
git clone https://github.com/TheBoringRats/ratcrawler.git
cd ratcrawler

# Build Docker image
docker build -t ratcrawler .

# Run container
docker run -it ratcrawler
```

## Detailed Installation

### Python Dependencies

The following Python packages are required:

```txt
beautifulsoup4>=4.11.0
requests>=2.28.0
lxml>=4.9.0
sqlite3
networkx>=3.0
pandas>=1.5.0
numpy>=1.21.0
newspaper3k>=0.2.8
feedparser>=6.0.0
selenium>=4.5.0
webdriver-manager>=3.8.0
```

### Installing from requirements.txt

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install in virtual environment
python3 -m venv ratcrawler_env
source ratcrawler_env/bin/activate  # On Windows: ratcrawler_env\Scripts\activate
pip install -r requirements.txt
```

### Manual Installation

```bash
# Core dependencies
pip install beautifulsoup4 requests lxml sqlite3 networkx pandas numpy

# Web scraping dependencies
pip install newspaper3k feedparser selenium webdriver-manager

# Optional: Data visualization
pip install plotly dash
```

## Rust Installation

### Installing Rust

```bash
# Install Rust using rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Verify installation
rustc --version
cargo --version
```

### Building RatCrawler (Rust)

```bash
# Navigate to Rust version
cd rust_version

# Build in debug mode
cargo build

# Build optimized release version
cargo build --release

# Run tests
cargo test

# Generate documentation
cargo doc --open
```

## Configuration

### Environment Setup

Create a `.env` file in the project root:

```bash
# Database configuration
DATABASE_URL=sqlite:///ratcrawler.db

# Crawler settings
USER_AGENT=RatCrawler/1.0
REQUEST_DELAY=1.5
MAX_PAGES=100
MAX_DEPTH=3

# API Keys (optional)
GOOGLE_TRENDS_API_KEY=your_key_here
TWITTER_API_KEY=your_key_here
```

### Database Setup

```bash
# Initialize database
python3 -c "
from database import DatabaseManager
db = DatabaseManager('ratcrawler.db')
db.initialize_database()
print('Database initialized successfully!')
"
```

## Verification

### Test Python Installation

```python
# test_installation.py
from crawler import EnhancedProductionCrawler
from backlinkprocessor import BacklinkProcessor

# Test basic functionality
crawler = EnhancedProductionCrawler({'max_pages': 5})
processor = BacklinkProcessor()

print("✅ RatCrawler Python installation successful!")
print(f"✅ Crawler version: {crawler.__class__.__name__}")
print(f"✅ Backlink processor ready: {processor.__class__.__name__}")
```

### Test Rust Installation

```bash
# Test Rust version
cd rust_version
cargo run -- --help

# Should display help information
```

## Troubleshooting

### Common Issues

#### Python Import Errors

```bash
# Update pip
pip install --upgrade pip

# Reinstall dependencies
pip uninstall -r requirements.txt
pip install -r requirements.txt
```

#### Rust Compilation Errors

```bash
# Update Rust
rustup update

# Clean and rebuild
cargo clean
cargo build
```

#### Permission Errors

```bash
# Fix permissions
chmod +x main.py
chmod +x rust_version/target/release/rat-crawler
```

### Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](../advanced/troubleshooting.md)
2. Search [GitHub Issues](https://github.com/TheBoringRats/ratcrawler/issues)
3. Create a new issue with detailed information

## Next Steps

Once installation is complete:

1. [Quick Start Guide](quick-start.md) - Your first crawl
2. [Configuration Guide](configuration.md) - Customize settings
3. [Web Crawling Guide](../features/web-crawling.md) - Learn core features
