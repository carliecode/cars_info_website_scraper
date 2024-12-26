import logging
from datetime import datetime

DATA_DIR = 'data'

PROXIES = [
        'http://8.219.97.248:80',
        'http://102.213.84.250:8080',
        'http://41.216.160.138:8082',
        'http://41.87.77.34:32650',
        'http://197.249.5.150:8443',
        'http://197.249.5.150:443',
        'http://43.246.200.142:9080',
        'http://103.239.253.118:58080',
    ]

current_time = datetime.now().strftime("%Y%m%d%H%M%S")
log_file = f"logs/cars_info_scraper_{current_time}.log"

def setup_logging(log_file=log_file, level=logging.INFO)-> logging.Logger:
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



   
