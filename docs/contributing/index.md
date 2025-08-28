---
layout: default
title: Contributing
nav_order: 7
description: "How to contribute to RatCrawler"
---

# Contributing to RatCrawler

We welcome contributions from the community! This guide explains how to get involved in the RatCrawler project.

## Ways to Contribute

### 🐛 Report Bugs

Found a bug? Help us fix it!

- [GitHub Issues](https://github.com/TheBoringRats/ratcrawler/issues) - Report bugs here
- Include detailed steps to reproduce
- Add system information and error messages
- Suggest potential fixes if possible

### 💡 Request Features

Have an idea for a new feature?

- [GitHub Issues](https://github.com/TheBoringRats/ratcrawler/issues) - Request features here
- Describe the problem you're trying to solve
- Explain how the feature would work
- Consider alternative solutions

### 📝 Improve Documentation

Help make our documentation better!

- Fix typos and grammar errors
- Add missing information
- Improve code examples
- Create tutorials and guides

### 🧪 Write Tests

Improve code reliability!

- Write unit tests for new features
- Add integration tests
- Test edge cases and error conditions
- Improve test coverage

### 🔧 Code Contributions

Contribute code directly!

- Fix bugs and implement features
- Improve performance and efficiency
- Add new functionality
- Refactor and clean up code

## Development Setup

### Prerequisites

- **Python 3.8+** with pip
- **Rust 1.70+** (for Rust development)
- **Git** for version control
- **SQLite3** for database operations

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/TheBoringRats/ratcrawler.git
cd ratcrawler

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install
```

### Project Structure

```
ratcrawler/
├── 🏠 main.py                 # Main entry point
├── 🕷️ crawler.py              # Core crawler logic
├── 🔗 backlinkprocessor.py    # Backlink analysis
├── 🗄️ crawlerdb.py            # Database operations
├── ⚙️ config.py               # Configuration
├── 📊 trend_analyzer.py       # Trend analysis
├── 🌱 seed_urls.json          # Seed URLs
├── 🧪 test_*.py               # Test files
├── 📋 requirements.txt        # Python dependencies
└── 📊 engine/                 # Trend analysis engine
    ├── 📈 googletrends.py     # Google Trends
    ├── 📱 social_trends.py    # Social media
    ├── 💰 financial_trends.py # Financial data
    └── 📰 news_trends.py      # News analysis
```

## Development Workflow

### 1. Choose an Issue

- Check [GitHub Issues](https://github.com/TheBoringRats/ratcrawler/issues) for open tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Branch

```bash
# Create and switch to new branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes

- Write clear, concise commit messages
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes

```bash
# Run tests
python3 -m pytest

# Run specific test file
python3 -m pytest test_crawler.py

# Run with coverage
python3 -m pytest --cov=ratcrawler

# Test Rust code
cd rust_version
cargo test
```

### 5. Commit and Push

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add new crawling feature

- Add support for custom user agents
- Improve error handling for network timeouts
- Add comprehensive tests"

# Push to your branch
git push origin feature/your-feature-name
```

### 6. Create Pull Request

- Go to [GitHub](https://github.com/TheBoringRats/ratcrawler/pulls)
- Click "New Pull Request"
- Select your branch as the compare branch
- Fill out the pull request template
- Request review from maintainers

## Coding Standards

### Python Code Style

We follow PEP 8 with some modifications:

```python
# Good: Clear variable names
def crawl_website(url, max_depth=3):
    """Crawl a website with specified depth."""
    pass

# Bad: Unclear abbreviations
def crawl(url, md=3):
    pass
```

**Key Guidelines:**

- Use 4 spaces for indentation
- Maximum line length: 88 characters
- Use descriptive variable and function names
- Add docstrings to all public functions
- Use type hints where possible

### Rust Code Style

Follow standard Rust conventions:

```rust
// Good: Clear, idiomatic Rust
pub fn crawl_website(url: &str, max_depth: usize) -> Result<CrawlResult, CrawlerError> {
    // Implementation
}

// Bad: Non-idiomatic
pub fn crawl(url: String, depth: i32) -> CrawlResult {
    // Implementation
}
```

### Commit Message Format

We use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions
- `chore`: Maintenance tasks

**Examples:**

```bash
git commit -m "feat: add multi-source trend analysis

- Support Google Trends, social media, and financial data
- Add sentiment analysis capabilities
- Include comprehensive test coverage"

git commit -m "fix: resolve memory leak in crawler

- Fix connection pool not being properly closed
- Add proper cleanup in error scenarios
- Add memory usage tests"

git commit -m "docs: update API reference

- Add missing method documentation
- Include code examples for all endpoints
- Fix parameter descriptions"
```

## Testing

### Unit Tests

```python
# test_crawler.py
import pytest
from crawler import EnhancedProductionCrawler

class TestEnhancedProductionCrawler:
    def test_initialization(self):
        config = {'delay': 1.0, 'max_pages': 10}
        crawler = EnhancedProductionCrawler(config)
        assert crawler.config['delay'] == 1.0

    def test_crawl_single_url(self):
        crawler = EnhancedProductionCrawler()
        # Mock HTTP response
        result = crawler.crawl_single_url('https://httpbin.org/html')
        assert 'title' in result
        assert 'content' in result
```

### Integration Tests

```python
# test_integration.py
def test_full_crawling_workflow():
    """Test complete crawling workflow."""
    crawler = EnhancedProductionCrawler({
        'max_pages': 5,
        'delay': 0.1
    })

    urls = ['https://httpbin.org/html']
    results = crawler.comprehensive_crawl(urls)

    assert results['total_pages'] > 0
    assert len(results['successful_crawls']) > 0
    assert 'crawl_duration' in results
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest test_crawler.py

# Run tests with coverage
pytest --cov=ratcrawler --cov-report=html

# Run Rust tests
cd rust_version && cargo test
```

## Documentation

### Adding Documentation

1. **Code Documentation**: Add docstrings to all public functions
2. **API Documentation**: Update API reference for new endpoints
3. **User Guides**: Create tutorials for new features
4. **Examples**: Add code examples to documentation

### Documentation Standards

```python
def crawl_website(url, max_depth=3, delay=1.0):
    """
    Crawl a website and extract content.

    This function performs a comprehensive crawl of the specified website,
    following links up to the maximum depth and respecting rate limits.

    Args:
        url (str): The starting URL to crawl
        max_depth (int): Maximum depth to follow links (default: 3)
        delay (float): Delay between requests in seconds (default: 1.0)

    Returns:
        dict: Crawl results containing:
            - successful_crawls: List of successfully crawled pages
            - failed_crawls: List of failed URLs with error messages
            - total_pages: Total number of pages processed
            - crawl_duration: Time taken for crawling

    Raises:
        NetworkError: If network connectivity issues occur
        ConfigurationError: If invalid configuration is provided

    Example:
        >>> results = crawl_website('https://example.com')
        >>> print(f"Crawled {results['total_pages']} pages")
        Crawled 15 pages
    """
    pass
```

## Pull Request Process

### Before Submitting

1. **Update Tests**: Ensure all tests pass
2. **Update Documentation**: Update docs for any new features
3. **Code Review**: Self-review your code
4. **Commit Messages**: Use conventional commit format
5. **Branch Status**: Ensure branch is up to date with main

### Pull Request Template

When creating a PR, please include:

```markdown
## Description

Brief description of the changes made.

## Type of Change

- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass

## Checklist

- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] Commit messages follow conventions
- [ ] Self-review completed

## Related Issues

Closes #123
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and checks
2. **Code Review**: Maintainers review code for quality and standards
3. **Testing**: Additional testing may be requested
4. **Approval**: PR approved and merged by maintainers

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn and contribute
- Maintain professional communication

### Getting Help

- **Documentation**: [Full Documentation](https://theboringrats.github.io/ratcrawler/)
- **Issues**: [GitHub Issues](https://github.com/TheBoringRats/ratcrawler/issues)
- **Discussions**: [GitHub Discussions](https://github.com/TheBoringRats/ratcrawler/discussions)
- **Contact**: [theboringrats@gmail.com](mailto:theboringrats@gmail.com)

### Recognition

Contributors are recognized through:

- GitHub contributor statistics
- Mention in release notes
- Attribution in documentation
- Community acknowledgments

## License

By contributing to RatCrawler, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Thank you for contributing to RatCrawler! Your efforts help make this project better for everyone in the community.
