#!/bin/bash
set -eu
cp /solution/fixed/ingest.py /app/opulse/ingest.py
cp /solution/fixed/buffer.py /app/opulse/buffer.py
cp /solution/fixed/segments.py /app/opulse/segments.py
cp /solution/fixed/learner.py /app/opulse/learner.py
rm -rf /app/opulse/__pycache__
cd /app
python3 -m opulse.cli --recordings /app/recordings --out /app/ledgers
