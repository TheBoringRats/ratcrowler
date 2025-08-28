from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import time
import asyncio
from typing import List, Dict, Any
import logging
import json
import os
import requests
from urllib.parse import urlparse
from datetime import datetime, timedelta
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from  dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XTrends:
    def __init__(self, headless: bool = True, username: str | None = None, password: str | None = None, cookies_file: str = "x_cookies.json"):
        self.headless = headless
        self.username = username
        self.password = password
        self.cookies_file = cookies_file
        driverpath = ChromeDriverManager().install()

        self.loginurl = "https://x.com/i/flow/login"
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")  # Mimic real browser
        if self.headless:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=ChromeService(driverpath), options=options)

    def save_cookies(self):
        """Save current session cookies to file"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"Cookies saved to {self.cookies_file}")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    def delete_cookies(self):
        """Delete saved cookies file"""
        try:
            if os.path.exists(self.cookies_file):
                os.remove(self.cookies_file)
                logger.info(f"Cookies file {self.cookies_file} deleted")
            else:
                logger.info("No cookies file to delete")
        except Exception as e:
            logger.error(f"Failed to delete cookies file: {e}")

    async def load_cookies(self):
        """Load cookies from file and add them to the driver"""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)

                # Go to X.com first to set the domain
                self.driver.get("https://x.com")
                await asyncio.sleep(3)

                # Add each cookie
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.debug(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")

                logger.info(f"Cookies loaded from {self.cookies_file}")
                return True
            else:
                logger.info("No cookies file found")
                return False
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False

    async def is_logged_in(self):
        """Check if user is already logged in"""
        try:
            self.driver.get("https://x.com/home")
            await asyncio.sleep(5)

            # Check if we're redirected to login page or if we can access home
            current_url = self.driver.current_url
            if "login" in current_url or "flow" in current_url:
                return False
            elif "home" in current_url or "x.com" in current_url:
                try:
                    self.driver.find_element(By.XPATH, "//a[@data-testid='SideNav_NewTweet_Button']")
                    return True
                except NoSuchElementException:
                    try:
                        self.driver.find_element(By.XPATH, "//div[@data-testid='SideNav_AccountSwitcher_Button']")
                        return True
                    except NoSuchElementException:
                        return False
            return False
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False

    async def login_with_cookies(self):
        """Try to login using saved cookies first, fallback to credential login"""
        cookies_loaded = await self.load_cookies()

        if cookies_loaded:
            logger.info("Checking if already logged in with cookies...")
            if await self.is_logged_in():
                logger.info("Successfully logged in using saved cookies!")
                return True
            else:
                logger.info("Cookies didn't work, proceeding with credential login...")

        success = await self.login()

        if success:
            await asyncio.sleep(2)
            self.save_cookies()

        return success

    async def login(self):
        if not self.username or not self.password:
            logger.error("Username and password must be provided for login.")
            return False

        try:
            self.driver.get(self.loginurl)
            await asyncio.sleep(10)

            wait = WebDriverWait(self.driver, 20)
            username_field = wait.until(EC.presence_of_element_located((By.NAME, "text")))
            username_field.clear()
            username_field.send_keys(self.username)

            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Next"]')))
            next_button.click()

            await asyncio.sleep(5)

            password_field = None
            password_selectors = [
                (By.NAME, "password"),
                (By.XPATH, "//input[@type='password']"),
                (By.CSS_SELECTOR, "input[name='password']"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@autocomplete='current-password']")
            ]

            for selector_type, selector_value in password_selectors:
                try:
                    password_field = wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                    logger.info(f"Found password field using selector: {selector_type}, {selector_value}")
                    break
                except TimeoutException:
                    logger.debug(f"Password field not found with selector: {selector_type}, {selector_value}")
                    continue

            if password_field is None:
                logger.error("Could not find password field with any selector")
                logger.debug(f"Current URL: {self.driver.current_url}")
                return False

            password_field.clear()
            password_field.send_keys(self.password)
            password_field.send_keys(Keys.RETURN)

            await asyncio.sleep(10)

            if "home" in self.driver.current_url or "x.com/home" in self.driver.current_url:
                logger.info("Login successful.")
                return True
            else:
                logger.error(f"Login failed. Current URL: {self.driver.current_url}")
                return False

        except NoSuchElementException as e:
            logger.error(f"Element not found during login: {e}")
            return False
        except TimeoutException as e:
            logger.error(f"Timeout during login: {e}")
            return False
        except Exception as e:
            logger.error(f"An error occurred during login: {e}")
            return False

    def close(self):
        """Close the browser driver"""
        if hasattr(self, 'driver'):
            self.driver.quit()

    async def scroll_to_load(self, max_scrolls: int = 30, sleep_time: float = 3.0):
        """Scroll the page to load more content, emulating deeper crawler depth"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for i in range(max_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(sleep_time)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info(f"No more content to load after {i+1} scrolls")
                break
            last_height = new_height
            logger.debug(f"Scrolled {i+1} times, new height: {new_height}")

    async def get_trending_topics(self) -> List[Dict[str, Any]]:
        """Get trending topics from last 24 hours using external archive (getdaytrends.com)"""
        trending_topics = []
        sources = [
            {"url": "https://getdaytrends.com/top/tweeted/day/", "category": "Most Tweeted"},
            {"url": "https://getdaytrends.com/top/longest/day/", "category": "Longest Trending"}
        ]

        for source in sources:
            try:
                logger.info(f"Navigating to {source['url']} for {source['category']} trends...")
                self.driver.get(source['url'])
                await asyncio.sleep(5)
                await self.scroll_to_load()  # Load more if available

                wait = WebDriverWait(self.driver, 20)

                # Extract from table rows
                row_selectors = [
                    "//table//tr[td]",  # Primary: table rows
                    "//div[contains(@class, 'trend-row')]"  # Fallback
                ]

                rows = []
                for selector in row_selectors:
                    try:
                        rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))
                        if rows:
                            logger.info(f"Found {len(rows)} trend rows with selector: {selector}")
                            break
                    except TimeoutException:
                        logger.debug(f"Timeout for selector: {selector}")

                if not rows:
                    logger.warning(f"No trends found for {source['url']}")
                    continue

                for i, row in enumerate(rows):
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td") or row.find_elements(By.TAG_NAME, "div")
                        if len(cells) < 3:
                            continue

                        rank = cells[0].text.strip()

                        # Robust trend extraction: Try <a> first, fallback to cell text
                        try:
                            trend_element = cells[1].find_element(By.TAG_NAME, "a")
                            trend_text = trend_element.text.strip()
                        except NoSuchElementException:
                            trend_text = cells[1].text.strip()

                        metric = cells[2].text.strip()  # tweets or duration

                        if trend_text:
                            trending_topics.append({
                                "trend_text": trend_text,
                                "category": source['category'],
                                "subtitle": "",
                                "metric": metric,  # Renamed from post_count for accuracy
                                "element_index": i
                            })
                    except StaleElementReferenceException:
                        logger.debug(f"Stale element for row {i} in {source['category']}")
                        continue
                    except Exception as e:
                        logger.debug(f"Error extracting row {i} in {source['category']}: {e}")

            except Exception as e:
                logger.error(f"Error scraping {source['url']}: {e}")

        # Unique by trend_text
        unique_trends = {t['trend_text']: t for t in trending_topics}.values()
        logger.info(f"Found {len(unique_trends)} unique trending topics from last 24 hours")
        return list(unique_trends)

    async def extract_post_data(self, post_element) -> Dict[str, Any]:
        """Extract data from a single post element, collect media URLs only"""
        post_data = {
            "text": "",
            "author": "",
            "timestamp": "",
            "images": [],
            "videos": [],
            "likes": "",
            "retweets": "",
            "replies": ""
        }

        try:
            # Extract post text
            text_selectors = [
                ".//div[@data-testid='tweetText']",
                ".//div[contains(@class, 'tweet-text')]",
                ".//span[contains(@class, 'css-901oao')]"
            ]

            for selector in text_selectors:
                try:
                    text_element = post_element.find_element(By.XPATH, selector)
                    if text_element:
                        post_data["text"] = text_element.text.strip()
                        break
                except NoSuchElementException:
                    continue

            # Extract author information
            try:
                author_element = post_element.find_element(By.XPATH, ".//div[@data-testid='User-Name']//span")
                post_data["author"] = author_element.text.strip()
            except NoSuchElementException:
                try:
                    author_element = post_element.find_element(By.XPATH, ".//a[contains(@href, '/')]//span")
                    post_data["author"] = author_element.text.strip()
                except NoSuchElementException:
                    pass

            # Extract timestamp
            try:
                time_element = post_element.find_element(By.XPATH, ".//time")
                post_data["timestamp"] = time_element.get_attribute("datetime")
            except NoSuchElementException:
                pass

            # Collect image URLs (no download)
            try:
                image_elements = post_element.find_elements(By.XPATH, ".//img[contains(@src, 'pbs.twimg.com')]")
                post_data["images"] = [img.get_attribute('src') for img in image_elements if img.get_attribute('src')]
            except Exception as e:
                logger.debug(f"Error extracting image URLs: {e}")

            # Collect video URLs (no download)
            try:
                video_elements = post_element.find_elements(By.XPATH, ".//video | .//source[@type='video/mp4']")
                post_data["videos"] = [v.get_attribute('src') for v in video_elements if v.get_attribute('src')]
            except Exception as e:
                logger.debug(f"Error extracting video URLs: {e}")

            # Extract engagement metrics
            engagement_selectors = {
                "likes": [".//div[@data-testid='like']", ".//div[contains(@aria-label, 'Like')]"],
                "retweets": [".//div[@data-testid='retweet']", ".//div[contains(@aria-label, 'Repost')]"],
                "replies": [".//div[@data-testid='reply']", ".//div[contains(@aria-label, 'Reply')]"]
            }

            for metric, selectors in engagement_selectors.items():
                for selector in selectors:
                    try:
                        element = post_element.find_element(By.XPATH, selector)
                        post_data[metric] = element.get_attribute('aria-label') or element.text.strip()
                        break
                    except NoSuchElementException:
                        continue

        except Exception as e:
            logger.error(f"Error extracting post data: {e}")

        return post_data

    async def scrape_trend_posts(self, trend_text: str, max_posts: int = 50) -> List[Dict[str, Any]]:
        """Scrape top posts for a specific trend, filtered to last 24 hours, with deeper scrolling"""
        posts = []

        try:
            logger.info(f"Scraping posts for trend: {trend_text}")

            # Search for the trend with latest mode
            search_url = f"https://x.com/search?q={trend_text.replace('#', '%23').replace(' ', '%20')}&src=trend_click&vertical=trends&f=live"
            self.driver.get(search_url)
            await asyncio.sleep(5)

            # Deeper scroll to load more posts
            await self.scroll_to_load(max_scrolls=30, sleep_time=3)

            # Wait for posts to load
            wait = WebDriverWait(self.driver, 10)
            post_selectors = [
                "//article[@data-testid='tweet']",
                "//div[@data-testid='tweet']",
                "//article[contains(@class, 'tweet')]"
            ]

            post_elements = []
            for selector in post_selectors:
                try:
                    elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))
                    if elements:
                        post_elements = elements
                        logger.info(f"Found {len(elements)} posts with selector: {selector}")
                        break
                except TimeoutException:
                    logger.debug(f"Post selector {selector} timed out")
                except Exception as e:
                    logger.debug(f"Post selector {selector} failed: {e}")

            if not post_elements:
                logger.warning("No post elements found")
                return posts

            # Extract data from each post, filter to last 24 hours
            for i, post_element in enumerate(post_elements):
                if len(posts) >= max_posts:
                    break
                try:
                    post_data = await self.extract_post_data(post_element)
                    # Filter to last 24 hours (UTC)
                    if post_data["timestamp"]:
                        try:
                            post_dt = datetime.strptime(post_data["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
                            if post_dt < datetime.utcnow() - timedelta(hours=24):
                                logger.debug(f"Skipping post {i+1} as it is older than 24 hours")
                                continue
                        except ValueError:
                            logger.debug(f"Invalid timestamp for post {i+1}: {post_data['timestamp']}")
                            continue
                    post_data["trend"] = trend_text
                    post_data["post_index"] = len(posts) + 1
                    posts.append(post_data)
                    await asyncio.sleep(1.5)  # Polite delay, increased for more requests
                except StaleElementReferenceException:
                    logger.debug(f"Stale element encountered for post {i+1}, skipping")
                    continue
                except Exception as e:
                    logger.error(f"Error processing post {i+1}: {e}")
                    continue

            logger.info(f"Successfully extracted {len(posts)} posts for trend: {trend_text} (filtered to last 24h)")

        except Exception as e:
            logger.error(f"Error scraping posts for trend {trend_text}: {e}")

        return posts

    async def scrape_trending_posts(self, max_trends: int = 30, posts_per_trend: int = 50) -> Dict[str, Any]:
        """Main method to scrape trending topics from last 24h and their posts"""
        results = {
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "trends": []
        }

        try:
            # Get trending topics from last 24h
            trending_topics = await self.get_trending_topics()

            if not trending_topics:
                logger.error("No trending topics found")
                return results

            # Use all unique, sliced to max_trends
            trending_topics = trending_topics[:max_trends]

            # Process each trend
            for i, trend in enumerate(trending_topics):
                logger.info(f"Processing trend {i+1}/{len(trending_topics)}: {trend['trend_text']}")
                try:
                    posts = await self.scrape_trend_posts(trend['trend_text'], posts_per_trend)

                    trend_data = {
                        "trend_text": trend['trend_text'],
                        "category": trend.get("category", ""),
                        "posts_count": len(posts),
                        "posts": posts
                    }

                    results["trends"].append(trend_data)

                except Exception as e:
                    logger.error(f"Error processing trend {trend['trend_text']}: {e}")
                    continue

            # Save results to file
            output_file = "xtrends.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"Results saved to {output_file}")
            logger.info(f"Scraped {len(results['trends'])} trends with {sum(len(t['posts']) for t in results['trends'])} total posts")

        except Exception as e:
            logger.error(f"Error in scrape_trending_posts: {e}")

        return results

async def main():
    username = os.getenv('X_USERNAME')
    password = os.getenv('X_PASSWORD')
    if not username or not password:
        logger.error("Set X_USERNAME and X_PASSWORD environment variables.")
        return

    x = XTrends(headless=True, username=username, password=password)
    try:
        success = await x.login_with_cookies()
        if success:
            logger.info("Login process completed successfully!")
            results = await x.scrape_trending_posts(max_trends=30, posts_per_trend=50)
            if results["trends"]:
                logger.info(f"Successfully scraped {len(results['trends'])} trends!")
                for trend in results["trends"]:
                    logger.info(f"- {trend['trend_text']} ({trend['category']}): {trend['posts_count']} posts")
            else:
                logger.warning("No trends were scraped")
            await asyncio.sleep(5)
        else:
            logger.error("Login process failed!")
    finally:
        x.close()

if __name__ == "__main__":
    asyncio.run(main())