import json
import logging
from datetime import datetime
from sqlalchemy import Date, create_engine, Table, Column, Integer, String, MetaData, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSON
import shutil
import os
import psycopg2


db_url = "postgresql://postgres:postgres@localhost:5432/postgres"


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


today_date = datetime.today().date()
logger = setup_logging()

engine = create_engine(db_url)
metadata = MetaData()

Session = sessionmaker(bind=engine)
session = Session()

def read_data_file(file_path: str) -> list[dict]:
    try:
        data = []
        with open(file_path, 'r', encoding='utf-8') as lines:
            for line in lines:
                data.append(line)
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading the file: {e}")
    return []

def write_to_db(json_data: list[dict], db_url: str, table_name: str) -> None:
    try:

        tbl = Table(
            table_name, 
            metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('url', String),
            Column('data', JSON),
            Column('extraction_date', Date)
        )
            
       
        tbl.create(engine, checkfirst=True)
            
        for item in json_data:
            item = json.loads(item)
            existing_record = session.query(tbl).filter(tbl.c.url == item['PageURL']).first()
            if existing_record:
                existing_record_data = existing_record.data
                if existing_record_data['AdvertPrice'] != item['AdvertPrice']:
                    update_stmt = tbl.update().where(tbl.c.url == item['PageURL']).values(data=str(item), extraction_date=today_date)
                    session.execute(update_stmt)
            else:
                insert_stmt = tbl.insert().values(data=item, url=item['PageURL'], extraction_date=today_date)
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

def main(file_to_read: str) -> None:
    data = read_data_file(file_to_read)
    write_to_db(
        data, 
        db_url=db_url,
        table_name='src_cars_information')
    move_file_to_archive(file_to_read, 'data/archive')

