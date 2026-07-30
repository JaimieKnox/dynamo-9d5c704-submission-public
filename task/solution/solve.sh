#!/bin/bash
set -eu

# The V-trace kernel, the sampler, the buffer, the shard ingestion, the segment builder, the
# epoch selection and the priority expression all already follow the contract. What is missing
# outright is the replay orchestration, together with the digest reduction and the differential
# diagnosis of the recorded production ledger, so that whole module is supplied.
cp /solution/fixed/learner.py /app/rlaudit/learner.py
rm -rf /app/rlaudit/__pycache__

cd /app
python3 -m rlaudit.cli --runs /app/runs --out /app/out
