"""Shard ingestion: the global admission order and per step visibility."""

import json
import os

NOTHING_VISIBLE = -1


def load_shards(bundle_dir):
    """Every recorded transition of the bundle in ascending global admission order."""
    sdir = os.path.join(bundle_dir, "shards")
    rows = []
    for name in sorted(os.listdir(sdir)):
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(sdir, name)) as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    rows.sort(key=lambda row: row["seq"])
    return rows


def load_admissions(bundle_dir):
    with open(os.path.join(bundle_dir, "ingest.json")) as handle:
        return json.load(handle)["admissions"]


def visible_seq(admissions, step, visibility_lag=0):
    """Highest watermark among ingest entries effective at this learner step."""
    best = NOTHING_VISIBLE
    found = False
    for entry in admissions:
        effective_from = entry["step"] - visibility_lag
        if step >= effective_from:
            if (not found) or entry["seq_watermark"] > best:
                best = entry["seq_watermark"]
                found = True
    return best if found else NOTHING_VISIBLE
