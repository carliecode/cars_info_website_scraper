import random
import time
import logging
import jsonlines
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import WebDriverException, DisconnectedException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, ResultSet, Tag

DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 1


def setup_logging(log_file='logs/app.log', level=logging.INFO):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


logger = setup_logging()


def get_random_user_agent() -> str:
    ua = UserAgent()
    return ua.random


def get_random_proxy() -> dict:
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
        options.add_argument(f"user-agent={get_random_user_agent()}")
        '''
        proxies = get_random_proxy()
        if proxies: 
            options.add_argument(f'--proxy-server={proxies["http"]}')
        '''
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(50)
        return driver
    except Exception as e:
        logger.error(f"Error configuring Chrome WebDriver: {str(e)}")
        raise


def restart_driver(driver: webdriver.Chrome ) -> webdriver.Chrome:
    
    if driver.service.process.poll() is not None:
        logger.info("WebDriver disconnected. Restarting...")
        driver.quit()
        driver = configure_chrome_driver()  # or configure_firefox_driver()
    return driver



def get_vehicle_tag_list(driver: webdriver.Chrome, url: str, retries: int = DEFAULT_RETRIES, backoff: int = DEFAULT_BACKOFF) -> ResultSet[Tag]:
    try:
        logger.info(f"Getting vehicles data from: {url}")
        
        driver = restart_driver(driver)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        listings = soup.select("div.masonry-item a.qa-advert-list-item")
        logger.info(f'{len(listings)} vehicles found')
        return listings
    except (WebDriverException, DisconnectedException ) as e:
        
        if retries > 0:
            wait_time = random.uniform(backoff, backoff * 2)
            logger.info(f'WebDriver is disconnected within get_vehicle_tag_list()')
            logger.info(f"Retrying get_vehicle_tag_list() in {wait_time}s... ({retries} retries left)")
            time.sleep(wait_time)
            driver = configure_chrome_driver()
            return get_vehicle_tag_list(driver, url, retries=retries -1, backoff=backoff)
        else:
            logger.error(f"get_vehicle_page_details(): {e.msg}")
            return []
    
    except Exception as e:
        
        logger.error(f"get_vehicle_tag_list(): {e.msg}")
        return []




def get_vehicle_page_details(driver: webdriver.Chrome, listing: Tag, listing_url: str, retries: int = DEFAULT_RETRIES, backoff: int = DEFAULT_BACKOFF) -> dict:

    details = {}

    try:
        advertPrice = listing.find('div', class_='qa-advert-price')
        advertPrice = advertPrice.text.strip() if advertPrice else 'NA'
        advertTitle = listing.find('div', class_='qa-advert-title')
        advertTitle = advertTitle.text.strip() if advertTitle else 'NA'
        descriptionText = listing.find('div', class_='b-list-advert-base__description-text')
        descriptionText = descriptionText.text.strip() if descriptionText else 'NA'
        regionText = listing.find('span', class_='b-list-advert__region__text')
        regionText = regionText.text.strip() if regionText else 'NA'

        details['AdvertPrice'] = advertPrice
        details['AdvertTitle'] = advertTitle
        details['DescriptionText'] = descriptionText
        details['RegionText'] = regionText

        time.sleep(random.uniform(2, 5))
        driver = restart_driver(driver)
        driver.get(listing_url)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        icon_attributes = soup.find_all('div', class_='b-advert-icon-attribute')
        for div in icon_attributes:
            itemprop_elements = div.find_all('span', attrs={'itemprop': True})
            for element in itemprop_elements:
                itemprop_name = str(element.get('itemprop'))
                itemprop_name = itemprop_name[0].upper() + itemprop_name[1:]
                itemprop_value = element.text.strip() if element.text.strip() else 'NA'
                details[itemprop_name] = itemprop_value

        attributes = soup.select("div.b-advert-attribute")
        for attr in attributes:
            key = attr.select_one("div.b-advert-attribute__key").text.strip().title().replace(' ','')
            value = attr.select_one("div.b-advert-attribute__value").text.strip()
            details[key] = value

        details['PageURL'] = listing_url

        logger.info(f"'{advertTitle}'  |  {len(details)} 'attributes found'  |  {listing_url}")
        return details
    except (WebDriverException, DisconnectedException ) as e:
        
        if retries > 0:
            wait_time = random.uniform(backoff, backoff * 2)
            logger.info(f'WebDriver is disconnected within get_vehicle_page_details()')
            logger.info(f"Retrying get_vehicle_page_details() in {wait_time}s... ({retries} retries left)")
            time.sleep(wait_time)
            driver = configure_chrome_driver()
            return get_vehicle_page_details(driver, listing, listing_url, retries=retries -1, backoff=backoff)
        else:
            logger.error(f"get_vehicle_page_details(): {e.msg}")
            return {}
    except Exception as e:
        logger.error(f"get_vehicle_page_details(): {e.msg}")
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

    base_url = "https://jiji.ng/cars?page="  
    max_pages = 1000  
    vehicles_count = 0
    vehicles = []

    try:
        
        driver = configure_chrome_driver()

        for page in range(1, max_pages + 1):

            url = f"{base_url}{page}"
            listings = get_vehicle_tag_list(driver, url)   

            if not listings:
                logger.error(f"{url} returned an empty car list")
                if page > 500:
                    break
                else:
                    continue
            for listing in listings:
                listing_url = 'https://jiji.ng' + listing['href']
                vehicle_details = get_vehicle_page_details(driver, listing, listing_url)
                if vehicle_details:  
                    vehicles.append(vehicle_details)
                time.sleep(random.uniform(2, 5))

            save_to_json_file(vehicles)
            vehicles_count = vehicles_count + len(vehicles)
            logger.info(f'Total vehicles processed: {vehicles_count}')
            logger.info('============================================')
            vehicles.clear()

    except Exception as e:
        logger.error(f"Error in scrape_car_prices function: {str(e)}")
    finally:
        driver.quit()
        logger.info(f"The program is exiting.")

if __name__ == "__main__":
    scrape_car_prices()
