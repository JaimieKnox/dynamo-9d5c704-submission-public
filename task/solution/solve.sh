#!/bin/bash
set -eu

# The V-trace kernel, the sampler, the buffer, the epoch selection and the priority
# expression already follow the contract. The replay orchestration is missing outright and the
# two helpers that carry the remaining stateful decisions deviate from it, so all three are
# supplied wholesale.
cp /solution/fixed/ingest.py /app/rlaudit/ingest.py
cp /solution/fixed/segments.py /app/rlaudit/segments.py
cp /solution/fixed/learner.py /app/rlaudit/learner.py
rm -rf /app/rlaudit/__pycache__

cd /app
python3 -m rlaudit.cli --runs /app/runs --out /app/out
python3 -m rlaudit.check --runs /app/runs --out /app/out
