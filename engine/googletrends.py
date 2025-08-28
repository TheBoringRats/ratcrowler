import feedparser
import xml.etree.ElementTree as ET
import requests
from newspaper import Article
from datetime import datetime, timedelta
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Major countries
major_countries = {
    "United States": "US",
    "India": "IN",
    "United Kingdom": "GB",
    "Germany": "DE",
    "France": "FR",
    "Canada": "CA",
    "Brazil": "BR",
    "Japan": "JP",
    "Australia": "AU",
    "Russia": "RU",
    "China": "CN",
    "South Korea": "KR",
    "Italy": "IT",
    "Spain": "ES",
    "Mexico": "MX",
    "Indonesia": "ID",
    "Saudi Arabia": "SA",
    "South Africa": "ZA",
    "Nigeria": "NG",
    "Turkey": "TR",
    "Argentina": "AR",
    "Netherlands": "NL",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Poland": "PL",
    "Norway": "NO",
    "Bangladesh": "BD",
    "Pakistan": "PK",
    "Vietnam": "VN",
    "Thailand": "TH",
    "Malaysia": "MY",
    "Philippines": "PH",
    "Egypt": "EG",
    "United Arab Emirates": "AE",
    "Singapore": "SG",
    "Israel": "IL",
    "Ukraine": "UA",
    "Belgium": "BE",
    "Austria": "AT",
    "Denmark": "DK",
    "Finland": "FI",
    "Ireland": "IE",
    "Portugal": "PT",
    "Greece": "GR",
    "Colombia": "CO",
    "Chile": "CL",
    "New Zealand": "NZ",
    "Czech Republic": "CZ",
    "Romania": "RO",
    "Hungary": "HU"
}


class GoogleTrends:
    def __init__(self):
        self.date_today = datetime.now()
        self.date_yesterday = self.date_today - timedelta(days=1)

    def _get_article_summary(self, link):
        """Get article summary with improved error handling and rate limiting."""
        if not link or not link.startswith(('http://', 'https://')):
            return "Invalid URL"

        try:
            # Add timeout and user agent
            article = Article(link, timeout=10)
            article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

            article.download()
            article.parse()

            # Check if article has meaningful content
            if article.text and len(article.text.strip()) > 100:
                # Try to get summary, fallback to text excerpt
                if hasattr(article, 'summary') and article.summary:
                    return article.summary[:500]  # Limit summary length
                else:
                    # Return first 300 characters of text as fallback
                    return article.text[:300] + "..." if len(article.text) > 300 else article.text
            else:
                return "Article content too short or unavailable"

        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str:
                logging.warning(f"Rate limited for article: {link}")
                return "Rate limited - summary not available"
            elif "404" in error_str or "not found" in error_str:
                return "Article not found"
            elif "403" in error_str or "forbidden" in error_str:
                return "Access forbidden"
            elif "timeout" in error_str:
                return "Request timeout"
            else:
                logging.warning(f"Failed to parse article {link}: {e}")
                return "Summary not available"

    def get_trends(self, limit_per_country=10, delay=3, skip_summaries=True, max_retries=3):
        """
        Get trends with improved error handling and retry logic.

        Args:
            limit_per_country: Maximum trends to fetch per country
            delay: Delay between requests in seconds
            skip_summaries: Whether to skip article summaries
            max_retries: Maximum number of retries for failed requests
        """
        all_trends = {}
        country_count = 0
        total_countries = len(major_countries)

        for country, code in major_countries.items():
            country_count += 1
            retries = 0

            while retries <= max_retries:
                try:
                    logging.info(f"Fetching trends for {country} ({code}) - {country_count}/{total_countries} (attempt {retries + 1})")

                    url = f"https://trends.google.com/trending/rss?geo={code}"
                    feed = feedparser.parse(url)

                    # Check for HTTP errors
                    if hasattr(feed, 'status'):
                        status_code = feed.status
                        if isinstance(status_code, int):
                            if status_code == 429:
                                logging.warning(f"Rate limited for {country}, waiting longer...")
                                time.sleep(delay * 2)
                                retries += 1
                                continue
                            elif status_code >= 400:
                                logging.warning(f"HTTP {status_code} for {country}")
                                break  # Don't retry for client/server errors

                    # Check if feed has entries
                    if not hasattr(feed, 'entries') or not feed.entries:
                        logging.warning(f"No entries found in feed for {country}")
                        break

                    country_trends = []
                    entries_processed = 0

                    for entry in feed.entries[:limit_per_country]:
                        try:
                            # Handle title extraction safely
                            raw_title = entry.get("title", "No Title")
                            if isinstance(raw_title, list):
                                trend_title = str(raw_title[0]) if raw_title else "No Title"
                            else:
                                trend_title = str(raw_title) if raw_title else "No Title"

                            trend_title = trend_title.strip()
                            if not trend_title or trend_title == "No Title":
                                continue

                            published = entry.get("published", "")
                            approx_traffic = entry.get("ht_approx_traffic", "Unknown")

                            # Extract news items
                            news_items = []
                            if hasattr(entry, 'ht_news_item'):
                                news_item = entry.ht_news_item
                                if isinstance(news_item, list):
                                    for item in news_item[:3]:  # Limit news items
                                        news_items.append({
                                            'title': getattr(item, 'ht_news_item_title', 'No Title'),
                                            'url': getattr(item, 'ht_news_item_url', ''),
                                            'source': getattr(item, 'ht_news_item_source', 'Unknown')
                                        })
                                else:
                                    news_items.append({
                                        'title': getattr(news_item, 'ht_news_item_title', 'No Title'),
                                        'url': getattr(news_item, 'ht_news_item_url', ''),
                                        'source': getattr(news_item, 'ht_news_item_source', 'Unknown')
                                    })

                            # Get summary if requested and we have valid news items
                            summary = "Summary skipped to avoid rate limiting"
                            if not skip_summaries and news_items:
                                valid_urls = [item['url'] for item in news_items if item['url']]
                                if valid_urls:
                                    summary = self._get_article_summary(valid_urls[0])

                            country_trends.append({
                                'trend_title': trend_title,
                                'approx_traffic': approx_traffic,
                                'published': published,
                                'news_items': news_items,
                                'summary': summary
                            })

                            entries_processed += 1

                        except Exception as e:
                            logging.warning(f"Error processing trend entry for {country}: {e}")
                            continue

                    all_trends[country] = country_trends
                    logging.info(f"Successfully fetched {len(country_trends)} trends for {country}")

                    # Success - break retry loop
                    break

                except Exception as e:
                    retries += 1
                    error_msg = str(e).lower()

                    if "timeout" in error_msg or "connection" in error_msg:
                        if retries <= max_retries:
                            logging.warning(f"Network error for {country}, retrying... ({retries}/{max_retries})")
                            time.sleep(delay)
                            continue
                        else:
                            logging.error(f"Failed to fetch {country} after {max_retries} retries: {e}")
                    else:
                        logging.error(f"Unexpected error for {country}: {e}")

                    all_trends[country] = []
                    break

            # Add delay between countries (only if not the last country)
            if country_count < total_countries:
                time.sleep(delay)

        return all_trends




def main():
    """Main function to fetch trends and save to JSON file with improved error handling."""
    import json
    import os
    import argparse

    try:
        # Setup argument parser
        parser = argparse.ArgumentParser(description='Google Trends Scraper')
        parser.add_argument('--limit', type=int, default=10, help='Number of trends per country')
        parser.add_argument('--delay', type=float, default=5.0, help='Delay between requests')
        parser.add_argument('--summaries', action='store_true', help='Include article summaries')
        parser.add_argument('--output', type=str, default='trends.json', help='Output file path')
        parser.add_argument('--max-retries', type=int, default=3, help='Maximum retries per country')

        args = parser.parse_args()

        logging.info("Starting Google Trends collection...")
        logging.info(f"Configuration: limit={args.limit}, delay={args.delay}, summaries={args.summaries}")

        trends_fetcher = GoogleTrends()

        # Fetch trends with improved parameters
        trends = trends_fetcher.get_trends(
            limit_per_country=args.limit,
            delay=args.delay,
            skip_summaries=not args.summaries,
            max_retries=args.max_retries
        )

        # Save to JSON file
        output_file = args.output
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(trends, f, indent=2, ensure_ascii=False)

        # Verify file was created and has content
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            logging.info(f"Trends saved to {output_file} (Size: {file_size:,} bytes)")

            # Count total trends collected
            total_trends = sum(len(country_trends) for country_trends in trends.values())
            countries_with_data = sum(1 for country_trends in trends.values() if len(country_trends) > 0)
            countries_without_data = len(trends) - countries_with_data

            logging.info(f"Collection complete:")
            logging.info(f"  - Total trends: {total_trends:,}")
            logging.info(f"  - Countries with data: {countries_with_data}")
            logging.info(f"  - Countries without data: {countries_without_data}")

            if countries_without_data > 0:
                no_data_countries = [country for country, trends_list in trends.items() if not trends_list]
                logging.info(f"  - Countries with no trends: {', '.join(no_data_countries[:5])}{'...' if len(no_data_countries) > 5 else ''}")

        else:
            logging.error(f"Failed to create {output_file} file")
            return 1

    except KeyboardInterrupt:
        logging.info("Collection interrupted by user")
        return 1
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
