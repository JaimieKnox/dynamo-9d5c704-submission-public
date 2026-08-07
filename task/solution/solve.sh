#!/bin/bash
set -eu
cp /solution/fixed/gae.py /app/gaegrid/gae.py
cp /solution/fixed/ledger.py /app/gaegrid/ledger.py
rm -rf /app/gaegrid/__pycache__
cd /app
python3 -m gaegrid.cli --packs /app/packs --out /app/reports
