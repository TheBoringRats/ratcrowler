# RatCrawler Documentation

This directory contains the complete documentation for RatCrawler, hosted on GitHub Pages.

## 📁 Documentation Structure

```
docs/
├── _config.yml              # Jekyll configuration
├── index.md                 # Main documentation page
├── getting-started/
│   ├── installation.md      # Installation guide
│   └── quick-start.md       # Quick start tutorial
├── features/
│   └── web-crawling.md      # Web crawling features
├── api-reference/
│   └── index.md             # Complete API reference
├── contributing/
│   └── index.md             # Contributing guide
└── README.md                # This file
```

## 🚀 GitHub Pages Setup

### Automatic Deployment

This documentation is automatically deployed to GitHub Pages when:

1. **Repository Settings**: GitHub Pages is enabled for the `docs/` folder
2. **Push to Main**: Changes pushed to the `main` branch trigger deployment
3. **Jekyll Build**: GitHub automatically builds the site using Jekyll

### Manual Testing

To test the documentation locally before deploying:

```bash
# Install Jekyll and dependencies
gem install jekyll bundler

# Navigate to docs directory
cd docs

# Install dependencies
bundle install

# Serve locally
bundle exec jekyll serve

# View at http://localhost:4000
```

## 📝 Writing Documentation

### File Structure

- Use Markdown (`.md`) files for all documentation
- Organize content in logical directories
- Use Jekyll front matter for metadata

### Front Matter

Each documentation page should include front matter:

```yaml
---
layout: default
title: "Page Title"
nav_order: 1
parent: Parent Section (optional)
description: "Brief description for SEO"
permalink: /custom/path/ (optional)
---
```

### Navigation

Pages are automatically organized in the navigation based on:

- `nav_order`: Controls the order in navigation
- `parent`: Creates hierarchical navigation
- Directory structure: Files in subdirectories create sections

### Writing Guidelines

#### Headings

```markdown
# Page Title (H1 - only one per page)

## Section (H2)

### Subsection (H3)

#### Sub-subsection (H4)
```

#### Code Blocks

```python
# Python code
def example_function():
    return "Hello, World!"
```

```bash
# Terminal commands
echo "Hello, World!"
```

#### Lists

```markdown
- Item 1
- Item 2
  - Nested item
  - Another nested item
- Item 3
```

#### Links

```markdown
[Link Text](url)
[Relative Link](../path/to/file.md)
[API Reference](../api-reference/index.md)
```

#### Tables

```markdown
| Column 1 | Column 2 | Column 3 |
| -------- | -------- | -------- |
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

## 🎨 Styling and Themes

### Default Theme

The documentation uses Jekyll's Minima theme with custom styling:

- **Clean Design**: Minimal, distraction-free layout
- **Responsive**: Works on desktop, tablet, and mobile
- **Dark Mode**: Automatic dark/light mode switching
- **Search**: Built-in search functionality

### Custom CSS

Add custom styles in `docs/assets/css/main.scss`:

```scss
// Custom styles
.site-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.page-content {
  max-width: 1200px;
}
```

## 🔍 SEO and Metadata

### Page Metadata

Each page includes:

- **Title**: Page title in browser tab
- **Description**: SEO description
- **Keywords**: Automatically generated from content
- **Canonical URL**: Prevents duplicate content issues

### Site Metadata

Configured in `_config.yml`:

```yaml
title: "RatCrawler Documentation"
description: "Comprehensive web crawler and multi-source trending analysis system"
author: TheBoringRats
```

## 📊 Analytics and Tracking

### GitHub Insights

Track documentation usage through:

- **Page Views**: GitHub provides traffic analytics
- **Popular Content**: See which pages are most visited
- **Referral Sources**: Understand how users find the docs

### Custom Analytics (Optional)

Add Google Analytics or similar:

```html
<!-- Add to _includes/head.html -->
<script
  async
  src="https://www.googletagmanager.com/gtag/js?id=GA_TRACKING_ID"
></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    dataLayer.push(arguments);
  }
  gtag("js", new Date());
  gtag("config", "GA_TRACKING_ID");
</script>
```

## 🔄 Maintenance

### Regular Updates

- **Review Content**: Regularly check for outdated information
- **Update Examples**: Ensure code examples work with current versions
- **Fix Links**: Check for broken internal and external links
- **Performance**: Optimize images and large files

### Version Management

- **Version Badges**: Show current version in documentation
- **Changelog**: Document significant changes
- **Deprecation Notices**: Warn about deprecated features

## 🤝 Contributing to Documentation

### Content Guidelines

1. **Be Clear**: Use simple, straightforward language
2. **Be Comprehensive**: Cover all aspects of the topic
3. **Be Consistent**: Follow established patterns and conventions
4. **Be Current**: Keep information up to date

### Review Process

1. **Self-Review**: Check your own work before submitting
2. **Peer Review**: Have others review technical accuracy
3. **Technical Review**: Ensure code examples work
4. **Editorial Review**: Check grammar, spelling, and clarity

### Tools and Resources

- **Markdown Linter**: Use tools like `markdownlint` for consistency
- **Link Checker**: Tools like `lychee` to find broken links
- **Spell Checker**: Check spelling and grammar
- **Accessibility Checker**: Ensure content is accessible

## 📞 Support

### Getting Help

- **Documentation Issues**: [GitHub Issues](https://github.com/TheBoringRats/ratcrawler/issues)
- **General Questions**: [GitHub Discussions](https://github.com/TheBoringRats/ratcrawler/discussions)
- **Contact**: [theboringrats@gmail.com](mailto:theboringrats@gmail.com)

### Resources

- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [GitHub Pages Guide](https://docs.github.com/en/pages)
- [Markdown Guide](https://www.markdownguide.org/)
- [Minima Theme](https://github.com/jekyll/minima)

---

## 🚀 Deployment Checklist

Before deploying documentation updates:

- [ ] Test locally with `bundle exec jekyll serve`
- [ ] Check for broken links
- [ ] Validate all code examples
- [ ] Review for spelling and grammar
- [ ] Ensure mobile responsiveness
- [ ] Test search functionality
- [ ] Verify all images load correctly
- [ ] Check page load performance

## 📈 Success Metrics

Track documentation effectiveness:

- **Page Views**: Monitor traffic to documentation
- **Time on Page**: Measure engagement
- **Search Queries**: Analyze what users are looking for
- **Issue Resolution**: Track if docs reduce support requests
- **User Feedback**: Collect feedback on documentation quality

---

<div style="text-align: center; margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
  <p><strong>📖 Happy documenting! 📖</strong></p>
  <p>Built with ❤️ by TheBoringRats</p>
</div>
