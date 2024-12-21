Cars Information Scraper
==========================
Table of Contents
(#overview)
(#requirements)
(#installation)
(#usage)
(#functionality)
(#error-handling)
(#logging)
(#contributing)

Overview
-----------
This is a web scraping script designed to extract car price information from Jiji.ng, a Nigerian online marketplace.

Requirements
------------
Python 3.8+
Selenium WebDriver
ChromeDriver
Fake UserAgent
jsonlines
logging

Installation
------------
Clone this repository: git clone https://github.com/carliecode/jiji-ng-car-price-scraper.git
Install required packages: pip install -r requirements.txt
Configure ChromeDriver and WebDriver settings in configure_chrome_driver() function

Usage
-----
Run the script: python scrape_car_prices.py
The script will extract car price information from Jiji.ng and save it to a JSON file named "data.json"

Functionality
------------
Extracts car price information from Jiji.ng
Uses Selenium WebDriver and ChromeDriver for web scraping
Employs fake UserAgent rotation for anonymity
Saves extracted data to a JSON file
Logs errors and exceptions

Error Handling
-------------
Catches and logs WebDriver exceptions
Handles errors during data extraction and storage
Retries failed requests with exponential backoff

Logging
-------
Logs errors, exceptions, and script progress
Uses Python's built-in logging module
Configurable logging settings in setup_logging() function

Contributing
------------
Fork this repository and submit pull requests
Report issues and bugs
Improve code quality and functionality

License
-------
In progress

Acknowledgments
---------------
Jiji.ng for providing car price information
Selenium and ChromeDriver for web scraping functionality
Fake UserAgent for anonymity
