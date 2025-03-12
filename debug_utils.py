import logging
from datetime import datetime
import os

def setup_logger():
    # Debug mappa létrehozása ha még nem létezik
    debug_path = os.path.join(os.getcwd(), 'debug')
    if not os.path.exists(debug_path):
        os.makedirs(debug_path)
        print(f"DEBUG: Created debug directory at {debug_path}")

    # Logger konfigurálása
    log_file = os.path.join(debug_path, f'debug_{datetime.now().strftime("%Y%m%d")}.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    print(f"DEBUG: Logger initialized, writing to {log_file}")
