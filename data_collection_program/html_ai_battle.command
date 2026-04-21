#!/bin/bash
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sleep 1 && open http://127.0.0.1:5000 &
python app.py
