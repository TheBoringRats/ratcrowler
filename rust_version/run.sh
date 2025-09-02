#!/bin/bash
# Build and run script for RatCrawler Rust version

echo "🐀 Building RatCrawler Rust Version..."

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Cargo not found. Please install Rust first: https://rustup.rs/"
    exit 1
fi

# Build the project
echo "📦 Building project..."
cargo build --release

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "🚀 Starting RatCrawler..."
    echo "📊 Dashboard will be available at: http://localhost:8080"
    echo "🛑 Press Ctrl+C to stop"
    echo ""

    # Run the application
    cargo run --release
else
    echo "❌ Build failed!"
    exit 1
fi
