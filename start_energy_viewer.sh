#!/bin/bash
# Virtuális környezet aktiválása
source /home/tibor/PythonProjects/energia_monitoring/venv/bin/activate

# Váltás a projekt könyvtárba
cd /home/tibor/PythonProjects/energia_monitoring

# CSV monitor indítása a háttérben
python src/csv_normalizer.py &

# Qt alkalmazás indítása
python qt_energy_viewer.py
