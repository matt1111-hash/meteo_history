# Energia Monitoring Rendszer

## Áttekintés
Ez a projekt egy komplex energia monitoring rendszer, amely képes:
- Automatikusan feldolgozni a bejövő energia mérési CSV fájlokat
- Valós időben monitorozni az új adatokat
- Vizualizálni és elemezni a fogyasztási adatokat
- Részletes riportokat készíteni (Excel, PDF)

## Komponensek

### 1. Qt Alapú Megjelenítő (qt_energy_viewer.py)
- Modern PyQt6 alapú grafikus felület
- Interaktív grafikonok és statisztikák
- Sötét/világos téma támogatás
- Export funkciók (Excel, PDF)
- Részletes statisztikai elemzések

### 2. CSV Monitor (csv_monitor.py)
- Háttérben futó szolgáltatás
- Figyeli a CSV-eredeti mappát
- Automatikusan feldolgozza az új fájlokat
- Valós idejű adatfrissítés

### 3. CSV Normalizáló (csv_normalizer.py)
- CSV fájlok egységesítése
- Kódolások kezelése
- Hibaellenőrzés és naplózás
- Adattisztítás

## Mappastruktúra
energia_monitoring/
├── CSV-eredeti/     # Ide érkeznek az új CSV fájlok
├── CSV-normalis/    # A feldolgozott, egységesített adatok
├── export/          # Exportált Excel és PDF fájlok
├── logs/           # Naplófájlok
└── scripts/        # Python szkriptek
