from bs4 import BeautifulSoup, ResultSet, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from fake_useragent import UserAgent
import random
import time
import os
import logging
import logging.config
import json
import yaml

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

def configure_chrome_driver() -> webdriver.Chrome:
    try:
        options = ChromeOptions()
        options.add_argument("--headless")  # Comment this out for debugging
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--enable-unsafe-swiftshader")

        # Rotate user-agent
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f"user-agent={user_agent}")

        # Set up Chrome driver
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(50)  

        return driver
    except Exception as e:
        logger.error(f"Error configuring the Chrome WebDriver: {str(e)}", exc_info=False)
        raise

def configure_firefox_driver() -> webdriver.Firefox:
    try:
        options = FirefoxOptions()
        # options.add_argument("--headless")  # Comment this out for debugging
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # Rotate user-agent
        ua = UserAgent()
        user_agent = ua.random
        options.set_preference("general.useragent.override", user_agent)

        # Set up Firefox driver
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        driver.set_page_load_timeout(50)

        return driver
    except Exception as e:
        logger.error(f"Error configuring the Firefox WebDriver: {str(e)}", exc_info=False)
        raise

def get_driver(browser: str = "chrome") -> webdriver.Chrome | webdriver.Firefox:
    if browser == "firefox":
        return configure_firefox_driver()
    return configure_chrome_driver()

def scroll_to_bottom(driver: webdriver.Chrome | webdriver.Firefox) -> None:
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
        logger.error(f"Error while scrolling: {str(e)}", exc_info=False)

def get_car_listings(driver: webdriver.Chrome | webdriver.Firefox, url: str, retries: int = 3) -> ResultSet[Tag]:
    try:
        logger.info(f"Getting vehicles data from : { url}")
        driver.get(url)
        #scroll_to_bottom(driver)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        listings = soup.select("div.masonry-item a.qa-advert-list-item")
        logger.info(f'{len(listings)} vehicles were found')

        return listings
    except Exception as e:
        if retries > 0:
            logger.warning(f"Error while getting car Tags: {str(e)}. Retrying... ({retries} retries left)", exc_info=False)
            time.sleep(random.uniform(2, 5))
            return get_car_listings(driver, url, retries - 1)
        else:
            logger.error(f"Error while getting car Tags: {str(e)}", exc_info=False)
            return 

def get_listing_details(driver: webdriver.Chrome | webdriver.Firefox, listing: Tag, listing_url: str) -> dict:
    details = {}
    try:
        description = listing.find('div', class_='qa-advert-title')
        description = description.text.strip() if description else 'NA'

        #logger.info(f"Processing Tag - ''{description}''.... ")
        
        location = listing.find('span', class_='b-list-advert__region__text')
        location = location.text.strip() if location else 'NA'
        price = listing.find('div', class_='qa-advert-price')
        price  = price.text.strip() if price else 'NA'
        details['description'] = description
        details['location'] = location
        details['price'] = price

        #logger.info(f"Tag page - {listing_url}")
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

        logger.info(f"'{description}  ({len(details)} attr)': {listing_url}")      
        return details
    except Exception as e:
        logger.error(f"Error while extracting listing details: {str(e)}", exc_info=False)
        return {}

def save_to_json_file(data: list, filename: str = "data.json") -> None:
    try:
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Data must be a list of dictionaries")
        
        file_exists = os.path.isfile(filename)
        with open(filename, "a" if file_exists else "w", encoding="utf-8") as file:
            for item in data:
                if item:  # Ensure dictionary is not empty
                    file.write(json.dumps(item) + "\n")
        
        logger.info(f"Data {'appended to' if file_exists else 'written to'} {filename}", exc_info=False)
    
    except Exception as e:
        logger.error(f"Error saving data to file: {str(e)}", exc_info=False)

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
        logger.error(f"Error while rotating IP: {str(e)}", exc_info=False)
        return {}

def scrape_car_prices() -> None:
    base_url = "https://jiji.ng/cars?page="  # Base URL for pagination
    max_pages = 1000  # Set to the number of pages you want to scrape
    os.system('clear')
    vehicles = []
    try:
        driver = get_driver(browser="chrome")
        vehicles_count = 0
        
        for page in range(1, max_pages + 1):
            url = f"{base_url}{page}"
            listings = get_car_listings(driver, url)
            if not listings:
                break 
            for listing in listings:
                listing_url = 'https://jiji.ng' + listing['href']

                vehicle_details = get_listing_details(driver, listing, listing_url)
                if vehicle_details:  # Ensure dictionary is not empty
                    vehicles.append(vehicle_details)
                time.sleep(random.uniform(2, 5))
            save_to_json_file(vehicles)
            vehicles_count = vehicles_count + len(vehicles)
            logger.info(f'Total vehicles processed: {vehicles_count}')
            vehicles.clear()
    except Exception as e:
        logger.error(f"Error in main scraping function with Chrome: {str(e)}", exc_info=False)
        if driver: driver.quit()
        logger.info("Switching to Firefox", exc_info=False)
        try:
            driver = get_driver(browser="firefox")
            for page in range(1, max_pages + 1):
                url = f"{base_url}{page}"
                listings = get_car_listings(driver, url)
                if not listings:
                    break 
                for listing in listings:
                    listing_url = 'https://jiji.ng' + listing
                    vehicle_details = get_listing_details(driver, listing_url)
                    if vehicle_details:  # Ensure dictionary is not empty
                        vehicle_details.append(vehicle_details)
                    time.sleep(random.uniform(2, 5))
                save_to_json_file(vehicle_details)
                vehicles_count = vehicles_count + len(vehicles)
                logger.info(f'Total vehicles processed: {vehicles_count}')
                vehicles.clear()
        except Exception as e:
            logger.error(f"Error in main scraping function with Firefox: {str(e)}", exc_info=False)
        finally:
            if driver: driver.quit()
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    scrape_car_prices()