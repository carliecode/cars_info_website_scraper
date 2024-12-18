import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import random
import time
import os
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

def configure_driver():
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--enable-unsafe-swiftshader")

        # Rotate user-agent
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f"user-agent={user_agent}")

        # Comment out proxy settings for now 
        #proxy = rotate_ip() 
        #options.add_argument(f"--proxy-server={proxy['http']}")

        # Set up Chrome driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(50)  

        return driver
    except Exception as e:
        logger.error(f"Error configuring the WebDriver: {str(e)}")  # Log only the exception message
        raise

# Function to scroll to the bottom of the page until no new items are loaded
def scroll_to_bottom(driver):
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 5))  # Randomize sleep time to be less predictable
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        logger.info("Scrolled to bottom of the page")
    except Exception as e:
        logger.error(f"Error while scrolling: {str(e)}")

# Function to get car listings from a single page
def get_car_listings(driver, url, retries=3) -> list:
    try:
        logger.info(f"Accessing URL: {url}")
        driver.get(url)
        #scroll_to_bottom(driver)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        listings = soup.select("div.masonry-item a.qa-advert-list-item")

        logger.info(f'Loading a total of {len(listings)} car listings from {url}')
        return listings
    except Exception as e:
        if retries > 0:
            logger.warning(f"Error while getting car listings: {str(e)}. Retrying... ({retries} retries left)")
            time.sleep(random.uniform(2, 5))
            return get_car_listings(driver, url, retries - 1)
        else:
            logger.error(f"Error while getting car listings: {str(e)}")
            return []

# Function to extract listing details
def get_listing_details(driver, listing_url) -> dict:
    try:
        logger.info(f"Accessing listing URL: {listing_url}")
        driver.get(listing_url)  
        time.sleep(random.uniform(2, 5))  
        soup = BeautifulSoup(driver.page_source, "html.parser")
        details = {}
        
        attributes = soup.select("div.b-advert-attribute")
        for attr in attributes:
            key = attr.select_one("div.b-advert-attribute__key").text.strip()
            value = attr.select_one("div.b-advert-attribute__value").text.strip()
            details[key] = value  

        details['url'] = listing_url        
        return details
    except Exception as e:
        logger.error(f"Error while extracting listing details: {str(e)}")
        return {}

import json

def save_to_json_file(data, filename="data.json"):
    try:
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Data must be a list of dictionaries")
        
        file_exists = os.path.isfile(filename)
        with open(filename, "a" if file_exists else "w", encoding="utf-8") as file:
            for item in data:
                file.write(json.dumps(item) + "\n")
        
        print(f"Data {'appended to' if file_exists else 'written to'} {filename}")
    
    except Exception as e:
        print(f"Error saving data to file: {e}")


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
        logger.error(f"Error while rotating IP: {str(e)}")
        return {}

# Main scraping function with pagination
def scrape_car_prices():
    base_url = "https://jiji.ng/cars?page="  # Base URL for pagination
    max_pages = 100  # Set to the number of pages you want to scrape
    os.system('cls')
    all_details = []
    try:
        driver = configure_driver()
        
        for page in range(1, max_pages + 1):
            url = f"{base_url}{page}"
            listings = get_car_listings(driver, url)
            if not listings:
                break 
            for listing in listings:
                listing_url = 'https://jiji.ng' + listing["href"]  
                details = get_listing_details(driver, listing_url)
                all_details.append(details)
                time.sleep(random.uniform(2, 5))
            save_to_json_file(all_details)
            all_details.clear()
    except Exception as e:
        logger.error(f"Error in main scraping function: {str(e)}")
    finally:
        if driver: driver.quit()
        

if __name__ == "__main__":
    scrape_car_prices()
