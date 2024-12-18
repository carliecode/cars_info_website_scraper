import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager

from fake_useragent import UserAgent
import random
import time
import csv
import logging
import logging.config
import yaml

# Configure logging
def setup_logging(config_path='config/logging.yml'):
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
    except Exception as e:
        logging.basicConfig(level=logging.DEBUG)
        logging.error(f"Error loading logging configuration: {e}")
    return logging.getLogger(__name__)

logger = setup_logging()

# Configure Selenium WebDriver with user-agent rotation
def configure_driver():
    try:
        # Set up Chrome options
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Rotate user-agent
        from fake_useragent import UserAgent
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f"user-agent={user_agent}")

        # Set up Chrome driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver
    except Exception as e:
        logger.error(f"Error configuring the WebDriver: {e}")
        raise

# Function to scroll to the bottom of the page
def scroll_to_bottom(driver):
    try:
        prev_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 5))  # Randomize sleep time to be less predictable
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == prev_height:
                break
            prev_height = new_height
        logger.info("Scrolled to bottom of the page")
    except Exception as e:
        logger.error(f"Error while scrolling: {e}")

# Function to get car listings
def get_car_listings(driver, url):
    try:
        logger.info(f"Accessing URL: {url}")
        driver.get(url)
        scroll_to_bottom(driver)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        listings = soup.select("div.masonry-item a.qa-advert-list-item")
        logger.info(f"Found {len(listings)} listings")
        return listings
    except Exception as e:
        logger.error(f"Error while getting car listings: {e}")
        return []

# Function to extract listing details
def get_listing_details(driver, listing_url):
    try:
        logger.info(f"Accessing listing URL: {listing_url}")
        driver.get(listing_url)  # This line opens the link
        time.sleep(random.uniform(2, 5))  # Randomize sleep time to be less predictable
        soup = BeautifulSoup(driver.page_source, "html.parser")
        details = {}
         
        # Extract additional details from the specified element
        attributes = soup.select("div.b-advert-attribute")
        for attr in attributes:
            key = attr.select_one("div.b-advert-attribute__key").text.strip()
            value = attr.select_one("div.b-advert-attribute__value").text.strip()
            details[key] = value
        
        return details
    except Exception as e:
        logger.error(f"Error while extracting listing details: {e}")
        return {}

# Function to save data to CSV
def save_to_csv(data, filename="car_listings.csv"):
    try:
        if data:
            keys = data[0].keys()
            with open(filename, "w", newline="", encoding="utf-8") as output_file:
                dict_writer = csv.DictWriter(output_file, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(data)
            logger.info(f"Data saved to {filename}")
        else:
            logger.warning("No data to save.")
    except Exception as e:
        logger.error(f"Error saving data to CSV: {e}")

# Function to rotate IP address using a proxy list
def rotate_ip():
    try:
        proxies = [
            'http://8.219.97.248:80',
            'http://102.213.84.250:8080',
            'http://41.216.160.138:8082',
            'http://41.87.77.34:32650',
            'http://197.249.5.150:8443',
            'http://197.249.5.150:443',
            'http://43.246.200.142:9080',
            'http://103.239.253.118:58080',
        ]
        proxy = random.choice(proxies)
        return {"http": proxy, "https": proxy}
    except Exception as e:
        logger.error(f"Error while rotating IP: {e}")
        return {}

# Main scraping function
def scrape_car_prices():
    url = "https://jiji.ng/cars"  # Replace with the actual URL
    try:
        driver = configure_driver()
        listings = get_car_listings(driver, url)
        all_details = []
        for listing in listings:
            listing_url = url + listing["href"]  # Construct the full URL
            details = get_listing_details(driver, listing_url)
            all_details.append(details)
            time.sleep(random.uniform(2, 5))  # Randomize sleep time to be less predictable
    except Exception as e:
        logger.error(f"Error in main scraping function: {e}")
    finally:
        driver.quit()
        save_to_csv(all_details)

if __name__ == "__main__":
    scrape_car_prices()
