import os
import pandas as pd
import logging

# Naplózás beállítása
logging.basicConfig(
    filename="/home/tibor/PythonProjects/energia_monitoring/logs/csv_normalizer.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Mappák beállítása
input_folder = "/home/tibor/PythonProjects/energia_monitoring/CSV-eredeti"
output_folder = "/home/tibor/PythonProjects/energia_monitoring/CSV-normalis"
output_file = os.path.join(output_folder, "energia_adatok.csv")

# A többi kód marad ugyanaz...

# Ellenőrizzük, hogy a kimeneti mappa létezik-e
os.makedirs(output_folder, exist_ok=True)

# Új fájl létrehozása
logging.info("CSV normalizálás elindult...")

all_data = []

# Összes CSV fájl feldolgozása
for filename in os.listdir(input_folder):
    if filename.endswith(".csv"):
        file_path = os.path.join(input_folder, filename)
        logging.info(f"📂 Feldolgozás: {file_path}")

        try:
            df = pd.read_csv(file_path, delimiter=";", encoding="cp1252")

            # Oszlopok egységesítése (Ha szükséges, ezt módosítsd az adatok szerkezetének megfelelően)
            expected_columns = [
                'Gyariszam', 'Azonosito', 'Kezdo_datum', 'Zaro_datum', 
                'Hatasos_ertek_kWh', 'Hatasos_statusz', 'Hatasos_vesz_ertek_kWh', 
                'Hatasos_vesz_statusz', 'Szaldo_ertek_kWh', 'Szaldo_statusz'
            ]
            df.columns = expected_columns[:len(df.columns)]  # Ha kevesebb oszlop van, ne legyen hiba

            # Dátumok konvertálása
            df['Kezdo_datum'] = pd.to_datetime(df['Kezdo_datum'], errors='coerce')
            df['Zaro_datum'] = pd.to_datetime(df['Zaro_datum'], errors='coerce')

            # Csak érvényes adatokat tartunk meg
            df = df.dropna(subset=['Kezdo_datum', 'Zaro_datum', 'Hatasos_ertek_kWh'])

            all_data.append(df)

        except Exception as e:
            logging.error(f"⚠️ Hiba történt {filename} feldolgozásakor: {str(e)}")

# Adatok egyesítése és mentése
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    final_df.to_csv(output_file, index=False, sep=";", encoding="utf-8")
    logging.info(f"✅ Fájl elmentve: {output_file}")
else:
    logging.warning("⚠️ Nincsenek feldolgozható fájlok!")

print("📊 CSV feldolgozás befejezve!")

