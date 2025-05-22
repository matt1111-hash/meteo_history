#!/bin/bash
cd "$(dirname "$0")"

# CUDA kizárása Qt futás közben
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu
export QT_QPA_PLATFORM_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/qt6/plugins/platforms

# Venv aktiválása
if [ -f "./venv/bin/activate" ]; then
    echo "🔄 Virtuális környezet aktiválása..."
    source ./venv/bin/activate
else
    echo "⚠️ Nincs venv! Telepítsd: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# CSV normalizáló lefuttatása
echo "🧹 CSV normalizálás indítása..."
python3 src/csv_normalizer.py

# (Opcionális) CSV figyelő háttérben indítása
# echo "👀 CSV figyelő indítása háttérben..."
# python3 src/csv_monitor_safe.py &

# Energy Viewer indítása
echo "🚀 Energiafigyelő indítása..."
python3 qt_energy_viewer.py

