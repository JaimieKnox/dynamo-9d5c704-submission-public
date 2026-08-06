#!/bin/bash
set -eu
cp /solution/fixed/ingest.py /app/rlaudit/ingest.py
cp /solution/fixed/buffer.py /app/rlaudit/buffer.py
cp /solution/fixed/segments.py /app/rlaudit/segments.py
cp /solution/fixed/learner.py /app/rlaudit/learner.py
rm -rf /app/rlaudit/__pycache__
cd /app
python3 -m rlaudit.cli --runs /app/runs --out /app/out

# gate-sync
