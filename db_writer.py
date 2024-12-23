import json
import logging
from datetime import datetime
from sqlalchemy import Date, create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSON
import shutil
import os
import psycopg


def setup_logging(log_file='logs/db_writer_log.log', level=logging.INFO)-> logging.Logger:
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


db_url = "postgresql://postgres:postgres@localhost:5432/postgres"

today_date = datetime.today().date()
logger = setup_logging()

engine = create_engine(db_url)
metadata = MetaData()

metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def read_data_file(file_path: str) -> list[dict]:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from the file: {file_path}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading the file: {e}")
    return []

def write_to_db(json_data: list[dict], db_url: str, table_name: str) -> None:
    try:

        table = Table(table_name, metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('car_info', JSON),
        Column('extraction_date', Date))
        
        for item in json_data:
            existing_record = session.query(table).filter(table.c.car_info['PageURL'] == item['PageURL']).first()
            if existing_record:
                if existing_record.car_info['AdvertPrice'] != item['AdvertPrice']:
                    update_stmt = table.update().where(table.c.car_info['PageURL'] == item['PageURL']).values(car_info=item, extraction_date=today_date)
                    session.execute(update_stmt)
            else:
                insert_stmt = table.insert().values(car_info=item, extraction_date=today_date)
                session.execute(insert_stmt)

        session.commit()
        logger.info("Data successfully written to the database.")

    except Exception as e:
        logger.error(f"Error writing data to the database: {e}")
    finally:
        session.close()


def move_file_to_archive(file_path: str, archive_dir: str) -> None:
    try:
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        
        destination_path = os.path.join(archive_dir, os.path.basename(file_path))
        
        if os.path.exists(destination_path):
            os.remove(destination_path)
        
        shutil.move(file_path, destination_path)
        logger.info(f"File moved to archive: {destination_path}")
    except Exception as e:
        logger.error(f"Error moving file to archive: {e}")

def main(con_str: str, file_to_read: str = 'data.json') -> None:
    data = read_data_file(file_to_read)
    write_to_db(
        data, 
        db_url=con_str,
        table_name='src_cars_information')
    move_file_to_archive(file_to_read, 'data/archive')

