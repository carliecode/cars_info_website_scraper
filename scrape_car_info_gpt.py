import random
import time
import os
import logging
import jsonlines
import requests
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from contextlib import contextmanager
from bs4 import BeautifulSoup, ResultSet, Tag


# Configure logging
def setup_logging(log_file='logs/app.log', level=logging.INFO):
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=level,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


def rotate_ip() -> dict:
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

# Configure Chrome Driver
def configure_chrome_driver() -> webdriver.Chrome:
    try:
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--enable-unsafe-swiftshader")

        # Rotate User-Agent for every request
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f"user-agent={user_agent}")
        '''
        proxies = rotate_ip()
        if proxies: 
            options.add_argument(f'--proxy-server={proxies["http"]}')
        '''
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(50)
        return driver
    except Exception as e:
        logger.error(f"Error configuring Chrome WebDriver: {str(e)}")
        raise


# Configure Firefox Driver
def configure_firefox_driver() -> webdriver.Firefox:
    try:
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # Rotate User-Agent for every request
        ua = UserAgent()
        user_agent = ua.random
        options.set_preference("general.useragent.override", user_agent)
        '''
        proxies = rotate_ip()
        if proxies:
            options.set_preference("network.proxy.http", proxies["http"].split(":")[0])
            options.set_preference("network.proxy.http_port", int(proxies["http"].split(":")[1]))
            options.set_preference("network.proxy.ssl", proxies["http"].split(":")[0])
            options.set_preference("network.proxy.ssl_port", int(proxies["http"].split(":")[1]))
        '''
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        driver.set_page_load_timeout(50)
        return driver
    except Exception as e:
        logger.error(f"Error configuring Firefox WebDriver: {str(e)}")
        raise


@contextmanager
def get_driver(browser: str = "chrome"):
    driver = None
    try:
        driver = configure_chrome_driver() if browser == "chrome" else configure_firefox_driver()
        yield driver
    finally:
        if driver:
            driver.quit()


# Exponential Backoff Retry Logic
def get_car_listings(driver: webdriver.Chrome | webdriver.Firefox, url: str, retries: int = 3, backoff: int = 1) -> ResultSet[Tag]:
    try:
        logger.info(f"Getting vehicles data from: {url}")
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        listings = soup.select("div.masonry-item a.qa-advert-list-item")
        logger.info(f'{len(listings)} vehicles found')
        return listings
    except Exception as e:
        msg = str(e).split('Stacktrace:')[0].upper()
        if retries > 0:
            wait_time = random.uniform(backoff, backoff * 2)
            logger.warning(f"getting car listings: {msg}")
            logger.info("Retrying in {wait_time}s... ({retries} retries left)")
            time.sleep(wait_time)
            return get_car_listings(get_driver(), url, retries - 1, backoff * 2)  # Exponential backoff
        else:
            logger.warning(f"getting car listings: {msg}")
            return []


def get_listing_details(driver: webdriver.Chrome | webdriver.Firefox, listing: Tag, listing_url: str) -> dict:
    details = {}
    try:
        description = listing.find('div', class_='qa-advert-title')
        description = description.text.strip() if description else 'NA'
        location = listing.find('span', class_='b-list-advert__region__text')
        location = location.text.strip() if location else 'NA'
        price = listing.find('div', class_='qa-advert-price')
        price = price.text.strip() if price else 'NA'

        details['description'] = description
        details['location'] = location
        details['price'] = price

        driver.get(listing_url)
        time.sleep(random.uniform(2, 5))
        soup = BeautifulSoup(driver.page_source, "html.parser")

        item_condition = soup.find('span', itemprop='itemCondition')
        item_condition = item_condition.text.strip() if item_condition else 'NA'
        trans_type = soup.find('span', itemprop='vehicleTransmission')
        trans_type = trans_type.text.strip() if trans_type else 'NA'
        fuel_type = soup.find('span', itemprop='fuelType')
        fuel_type = fuel_type.text.strip() if fuel_type else 'NA'

        details['item_condition'] = item_condition
        details['trans_type'] = trans_type
        details['fuel_type'] = fuel_type

        attributes = soup.select("div.b-advert-attribute")
        for attr in attributes:
            key = attr.select_one("div.b-advert-attribute__key").text.strip()
            value = attr.select_one("div.b-advert-attribute__value").text.strip()
            details[key] = value

        details['page_url'] = listing_url

        logger.info(f"'{description}': {listing_url}")
        return details
    except Exception as e:
        logger.error(f"Error while extracting listing details: {str(e)}")
        return {}


def save_to_json_file(data: list, filename: str = "data.json") -> None:
    try:
        with jsonlines.open(filename, mode='a') as writer:
            for item in data:
                if item:  # Ensure dictionary is not empty
                    writer.write(item)
        logger.info(f"Data written to {filename}")
    except Exception as e:
        logger.error(f"Error saving data to file: {str(e)}")


def scrape_car_prices() -> None:
    base_url = "https://jiji.ng/cars?page="  # Base URL for pagination
    max_pages = 1000  # Set to the number of pages you want to scrape
    vehicles = []
    try:
        with get_driver(browser="chrome") as driver:
            vehicles_count = 0

            for page in range(1, max_pages + 1):
                url = f"{base_url}{page}"
                listings = get_car_listings(driver, url)
                if not listings:
                    logger.error(f"{url} returned an empty car list")
                    break
                for listing in listings:
                    listing_url = 'https://jiji.ng' + listing['href']
                    vehicle_details = get_listing_details(driver, listing, listing_url)
                    if vehicle_details:  # Ensure dictionary is not empty
                        vehicles.append(vehicle_details)
                    time.sleep(random.uniform(2, 5))

                save_to_json_file(vehicles)
                vehicles_count += len(vehicles)
                logger.info(f'Total vehicles processed: {vehicles_count}')
                vehicles.clear()

    except Exception as e:
        logger.error(f"Error in main scraping function: {str(e)}")
    finally:
        logger.info(f"The program is exiting.")

if __name__ == "__main__":
    scrape_car_prices()
