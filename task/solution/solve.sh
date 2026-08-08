#!/bin/bash
set -eu
cp /solution/fixed/seam.py /app/cutreturn/seam.py
cp /solution/fixed/register.py /app/cutreturn/register.py
cp /solution/fixed/successor.py /app/cutreturn/successor.py
cp /solution/fixed/cutmask.py /app/cutreturn/cutmask.py
cp /solution/fixed/gae.py /app/cutreturn/gae.py
cp /solution/fixed/ledger.py /app/cutreturn/ledger.py
rm -rf /app/cutreturn/__pycache__
cd /app
python3 -m cutreturn.cli --traces /app/traces --out /app/artifacts
