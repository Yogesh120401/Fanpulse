import os
import time
import pandas as pd
import logging
from bs4 import BeautifulSoup
from collections import OrderedDict

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from model import analyze_sentiment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TwitterHandler:
    def __init__(self):
        self.email    = "gokul2004330@gmail.com "
        self.username = "guestgoks2552"
        self.password = "Gokul&raj2552"
        self.driver   = None

    def _build_driver(self):
        """
        Build a stealth ChromeDriver compatible with Windows.
        """
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")

        driver = uc.Chrome(
            options=options,
            use_subprocess=True,  
            version_main=147,    # <-- Update this line to match your browser version
        )
        return driver

    def login(self):
        logger.info("Launching browser and navigating to Twitter login...")
        self.driver = self._build_driver()

        try:
            self.driver.get("https://x.com/i/flow/login")
            time.sleep(10)

            # Step 1: Email
            email_input = WebDriverWait(self.driver, 25).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            email_input.clear()
            email_input.send_keys(self.email)
            time.sleep(2)

            next_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[normalize-space()='Next']]")
                )
            )
            next_btn.click()
            time.sleep(5)

            # Step 2: Username challenge (optional)
            try:
                username_field = WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.NAME, "text"))
                )
                username_field.clear()
                username_field.send_keys(self.username)
                time.sleep(2)

                next_btn_2 = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[.//span[normalize-space()='Next']]")
                    )
                )
                next_btn_2.click()
                time.sleep(5)
            except TimeoutException:
                logger.info("No username challenge — continuing to password.")

            # Step 3: Password
            password_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(2)

            login_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[normalize-space()='Log in']]")
                )
            )
            login_btn.click()

            WebDriverWait(self.driver, 30).until(
                EC.url_contains("home")
            )
            logger.info("Login successful.")

        except Exception as e:
            logger.error(f"Login failed: {e}")
            if self.driver:
                self.driver.quit()
            raise

    def fetch_tweets(self, keyword, limit):
        search_url = f"https://x.com/search?q={keyword}&src=typed_query&f=live"
        logger.info(f"Searching for: '{keyword}'")

        try:
            self.driver.get(search_url)
            time.sleep(8)

            tweets = OrderedDict()
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            MAX_SCROLL_ATTEMPTS = 30
            scroll_attempts = 0

            while len(tweets) < limit and scroll_attempts < MAX_SCROLL_ATTEMPTS:
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                articles = soup.find_all("article")

                for article in articles:
                    text_div = article.find("div", {"data-testid": "tweetText"})
                    if text_div:
                        tweet = text_div.get_text(separator=" ", strip=True)
                        if tweet and tweet not in tweets:
                            tweets[tweet] = True
                    if len(tweets) >= limit:
                        break

                logger.info(f"Tweets collected: {len(tweets)}/{limit} "
                            f"(scroll {scroll_attempts + 1}/{MAX_SCROLL_ATTEMPTS})")

                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    logger.info("No more content to scroll.")
                    break

                last_height = new_height
                scroll_attempts += 1

        finally:
            if self.driver:
                self.driver.quit()

        return list(tweets.keys())[:limit]


def scrape_tweets(keyword="IPL", limit=20):
    handler = TwitterHandler()
    handler.login()
    raw_tweets = handler.fetch_tweets(keyword, limit)

    data = []
    logger.info("Running sentiment analysis...")

    for tweet in raw_tweets:
        try:
            sentiment, confidence = analyze_sentiment(tweet)
        except Exception as e:
            logger.warning(f"Skipping tweet — analysis error: {e}")
            sentiment, confidence = "Neutral", 0.5

        data.append({
            "Tweet": tweet,
            "Sentiment": sentiment,
            "Confidence": confidence,
            "Engagement Score": round(confidence * 100),
        })

    df = pd.DataFrame(data)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/tweets.csv", index=False)
    logger.info("Done.")
    return df


if __name__ == "__main__":
    df = scrape_tweets(keyword="Python", limit=10)
    print(df.head())