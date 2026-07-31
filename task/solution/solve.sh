#!/bin/bash
set -eu
cp /solution/fixed/learner.py /app/rlaudit/learner.py
cp /solution/fixed/params.py /app/rlaudit/params.py
cp /solution/fixed/segments.py /app/rlaudit/segments.py
rm -rf /app/rlaudit/__pycache__
cd /app
python3 -m rlaudit.cli --runs /app/runs --out /app/out

