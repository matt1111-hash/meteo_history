#!/bin/bash
cd "$(dirname "$0")"  # A script könyvtárába lép
source csv_converter_venv/bin/activate
python generate_graph.py

# A script végén deaktiváljuk a venv-et
deactivate
