import cars_info_agent 
import db_writer
from datetime import datetime
import os


def create_data_file() -> str:
    data_folder = os.path.join(os.getcwd(), 'data')
    os.makedirs(data_folder, exist_ok=True)
    
    file_name = datetime.now().strftime("%Y-%m-%d") + ".json"
    file_path = os.path.join(data_folder, file_name)
    
    if not os.path.exists(file_path):
        open(file_path, 'w').close()  # Create an empty file
    
    return file_path

def main():

    data_file = create_data_file()
    cars_info_agent.main(data_file)
    db_writer.main(data_file)


if __name__ == "__main__":
    main()

