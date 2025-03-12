import os
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# A mappák elérési útvonalai
input_folder = "/home/tibor/Projects/python_projects/energia_monitoring/CSV-eredeti"
output_folder = "/home/tibor/Projects/python_projects/energia_monitoring/CSV-normalis"
output_file = os.path.join(output_folder, "energia_adatok.csv")

# A fájlok figyelése
class Watcher(FileSystemEventHandler):
    def on_created(self, event):
        # Ha fájl jön létre és CSV típusú
        if event.is_directory:
            return
        if event.src_path.endswith(".csv"):  # Figyelje a CSV fájlokat
            print(f"Új fájl érkezett: {event.src_path}")
            self.process_new_file(event.src_path)

    def process_new_file(self, file_path):
        try:
            # Fájl beolvasása
            df = pd.read_csv(file_path)

            # Ellenőrizzük, hogy létezik-e az összesítő fájl
            if os.path.exists(output_file):
                # Ha igen, akkor olvassuk be és adjuk hozzá az új adatokat
                df_existing = pd.read_csv(output_file)
                df_combined = pd.concat([df_existing, df], ignore_index=True)
            else:
                # Ha nem létezik, hozzuk létre
                df_combined = df

            # Az összesítő fájl mentése
            df_combined.to_csv(output_file, index=False)
            print(f"Feldolgozva: {file_path} - Adatok hozzáadva az összesítőhöz.")
        except Exception as e:
            print(f"Hiba történt a fájl feldolgozása során: {e}")

# Observer elindítása
if __name__ == "__main__":
    event_handler = Watcher()
    observer = Observer()
    observer.schedule(event_handler, input_folder, recursive=False)

    print("Figyelem a CSV fájlokat...")
    observer.start()
    
    try:
        while True:
            time.sleep(1)  # Folyamatosan figyeljük a mappát
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
