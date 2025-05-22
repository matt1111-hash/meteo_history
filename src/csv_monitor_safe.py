import os
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import logging

# Naplózás beállítása
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_dir, "monitor.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Mappák dinamikus elérési útvonala
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
input_folder = os.path.join(base_dir, "CSV-eredeti")
output_folder = os.path.join(base_dir, "CSV-normalis")
output_file = os.path.join(output_folder, "energia_adatok.csv")

# Mappák létrehozása, ha nem léteznek
os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

# Figyelő eseménykezelő
class Watcher(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".csv"):
            logging.info(f"Új fájl érkezett: {event.src_path}")
            self.process_new_file(event.src_path)

    def process_new_file(self, file_path):
        try:
            df = pd.read_csv(file_path, delimiter=";", encoding="cp1252")
            df.columns = [
                'Gyariszam', 'Azonosito', 'Kezdo_datum', 'Zaro_datum', 
                'Hatasos_ertek_kWh', 'Hatasos_statusz', 'Hatasos_vesz_ertek_kWh', 
                'Hatasos_vesz_statusz', 'Szaldo_ertek_kWh', 'Szaldo_statusz'
            ][:len(df.columns)]

            df['Kezdo_datum'] = pd.to_datetime(df['Kezdo_datum'], errors='coerce')
            df['Zaro_datum'] = pd.to_datetime(df['Zaro_datum'], errors='coerce')
            df['Hatasos_ertek_kWh'] = df['Hatasos_ertek_kWh'].astype(str).str.replace(',', '.')
            df['Hatasos_ertek_kWh'] = pd.to_numeric(df['Hatasos_ertek_kWh'], errors='coerce')

            df = df.dropna(subset=['Kezdo_datum', 'Zaro_datum', 'Hatasos_ertek_kWh'])

            if os.path.exists(output_file):
                df_existing = pd.read_csv(output_file, delimiter=";", encoding="utf-8")
                df_combined = pd.concat([df_existing, df], ignore_index=True)
            else:
                df_combined = df

            df_combined.to_csv(output_file, index=False, sep=";", encoding="utf-8")
            logging.info(f"✅ Feldolgozva: {file_path}")
            print(f"Feldolgozva: {file_path}")

        except Exception as e:
            logging.error(f"❌ Hiba történt: {str(e)}")
            print(f"Hiba történt: {str(e)}")

# Figyelő elindítása
if __name__ == "__main__":
    print("Figyelem a CSV fájlokat...")
    logging.info("CSV monitor elindult.")
    event_handler = Watcher()
    observer = Observer()
    observer.schedule(event_handler, input_folder, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("CSV monitor leállt manuálisan.")

    observer.join()