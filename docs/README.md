# RatCrawler Documentation

This folder contains the complete documentation website for RatCrawler, built with HTML and Tailwind CSS for hosting on GitHub Pages.

## 📁 Files Structure

```
docs/
├── index.html          # Main homepage
├── api.html           # API documentation
├── examples.html      # Examples and tutorials
├── config.html        # Configuration guide
├── contributing.html  # Contributing guidelines
└── README.md         # This file
```

## 🚀 Hosting on GitHub Pages

### Option 1: Host from docs/ folder (Recommended)

1. **Go to your repository settings on GitHub**
2. **Navigate to "Pages" section**
3. **Under "Source", select "Deploy from a branch"**
4. **Choose "main" branch and "/docs" folder**
5. **Click "Save"**

Your documentation will be available at: `https://yourusername.github.io/ratcrawler/`

### Option 2: Host from root (Alternative)

If you prefer to host from the repository root:

1. **Move all HTML files from `docs/` to the repository root**
2. **Update internal links to remove `/docs/` prefix**
3. **In GitHub Pages settings, select "main" branch and "/" (root)**

## 🎨 Customization

### Colors and Styling

The documentation uses Tailwind CSS with a custom color scheme:

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: '#1f2937',    // Dark gray
                secondary: '#374151',  // Medium gray
                accent: '#3b82f6',     // Blue
                success: '#10b981',    // Green
                warning: '#f59e0b',    // Orange
                danger: '#ef4444'      // Red
            }
        }
    }
}
```

### Adding New Pages

1. **Create a new HTML file** following the existing structure
2. **Update navigation** in all HTML files to include the new page
3. **Add the page link** to the footer navigation
4. **Test locally** by opening the HTML files in a browser

### Modifying Content

- **Main content** is in the `<main>` or `<section>` tags
- **Navigation** is in the `<nav>` element at the top
- **Footer** contains links and copyright information
- **Styles** are defined in the `<style>` tag or Tailwind classes

## 🔧 Local Development

To test the documentation locally:

1. **Open any HTML file** in your web browser
2. **Navigate between pages** using the links
3. **Test responsiveness** by resizing your browser window
4. **Check all links** work correctly

## 📱 Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Clean, professional appearance with Tailwind CSS
- **Fast Loading**: Minimal dependencies, optimized for performance
- **SEO Friendly**: Proper meta tags and semantic HTML
- **Accessible**: Screen reader friendly with proper ARIA labels

## 🤝 Contributing to Documentation

When updating the documentation:

1. **Follow the existing structure** and styling patterns
2. **Test all links** and navigation
3. **Ensure mobile responsiveness**
4. **Update the table of contents** if adding new sections
5. **Keep the design consistent** across all pages

## 📞 Support

If you need help with the documentation:

- **Check existing issues** on GitHub
- **Create a new issue** with detailed description
- **Join the discussion** in GitHub Discussions
- **Check the contributing guide** for more information

## Built with ❤️ for the RatCrawler community

---

Built with ❤️ for the RatCrawler community
