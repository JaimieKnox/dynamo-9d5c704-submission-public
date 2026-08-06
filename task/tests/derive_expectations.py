"""Phase A: seal oracle ledgers, then remove the reference tree before pytest."""

from __future__ import annotations

import json
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SEALED_INPUTS = os.path.join(BASE, "inputs")
SEAL_PATH = os.path.join(BASE, "sealed_expectations.json")

# Every sealed fixture leaf must appear here (R185 / no_extraneous_files).
REQUIRED_INPUT_LEAVES = [
    "g01/features.json",
    "g01/ingest.json",
    "g01/manifest.json",
    "g01/params/epoch-00.json",
    "g01/params/epoch-01.json",
    "g01/params/epoch-02.json",
    "g01/params/epoch-03.json",
    "g01/params/epoch-04.json",
    "g01/shards/actor-00.jsonl",
    "g01/shards/actor-01.jsonl",
    "g01/shards/actor-02.jsonl",
    "g02/features.json",
    "g02/ingest.json",
    "g02/manifest.json",
    "g02/params/epoch-00.json",
    "g02/params/epoch-01.json",
    "g02/params/epoch-02.json",
    "g02/params/epoch-03.json",
    "g02/params/epoch-04.json",
    "g02/shards/actor-00.jsonl",
    "g02/shards/actor-01.jsonl",
    "g02/shards/actor-02.jsonl",
    "g02/shards/actor-03.jsonl",
    "g03/features.json",
    "g03/ingest.json",
    "g03/manifest.json",
    "g03/params/epoch-00.json",
    "g03/params/epoch-01.json",
    "g03/params/epoch-02.json",
    "g03/params/epoch-03.json",
    "g03/params/epoch-04.json",
    "g03/params/epoch-05.json",
    "g03/shards/actor-00.jsonl",
    "g03/shards/actor-01.jsonl",
    "g03/shards/actor-02.jsonl",
    "g04/features.json",
    "g04/ingest.json",
    "g04/manifest.json",
    "g04/params/epoch-00.json",
    "g04/params/epoch-01.json",
    "g04/shards/actor-00.jsonl",
    "g04/shards/actor-01.jsonl",
    "g04/shards/actor-02.jsonl",
    "g05/features.json",
    "g05/ingest.json",
    "g05/manifest.json",
    "g05/params/epoch-00.json",
    "g05/params/epoch-01.json",
    "g05/params/epoch-02.json",
    "g05/params/epoch-03.json",
    "g05/params/epoch-04.json",
    "g05/params/epoch-05.json",
    "g05/shards/actor-00.jsonl",
    "g05/shards/actor-01.jsonl",
    "g05/shards/actor-02.jsonl",
    "g05/shards/actor-03.jsonl",
    "g06/features.json",
    "g06/ingest.json",
    "g06/manifest.json",
    "g06/params/epoch-00.json",
    "g06/params/epoch-01.json",
    "g06/params/epoch-02.json",
    "g06/params/epoch-03.json",
    "g06/params/epoch-04.json",
    "g06/params/epoch-05.json",
    "g06/params/epoch-06.json",
    "g06/shards/actor-00.jsonl",
    "g06/shards/actor-01.jsonl",
    "g06/shards/actor-02.jsonl",
    "g06/shards/actor-03.jsonl",
    "g06/shards/actor-04.jsonl",
    "s01/features.json",
    "s01/ingest.json",
    "s01/manifest.json",
    "s01/params/epoch-00.json",
    "s01/shards/actor-00.jsonl",
    "s01/shards/actor-01.jsonl",
    "s02/features.json",
    "s02/ingest.json",
    "s02/manifest.json",
    "s02/params/epoch-00.json",
    "s02/shards/actor-00.jsonl",
    "s02/shards/actor-01.jsonl",
    "s03/features.json",
    "s03/ingest.json",
    "s03/manifest.json",
    "s03/params/epoch-00.json",
    "s03/shards/actor-00.jsonl",
    "s03/shards/actor-01.jsonl",
]


def _recording_directories(parent):
    names = []
    for candidate in os.listdir(parent):
        marker = os.path.join(parent, candidate, "manifest.json")
        if os.path.isfile(marker):
            names.append(candidate)
    return sorted(names)


def _assert_required_leaves():
    found = set()
    for root, _dirs, files in os.walk(SEALED_INPUTS):
        for name in files:
            full = os.path.join(root, name)
            found.add(os.path.relpath(full, SEALED_INPUTS).replace(os.sep, "/"))
    required = set(REQUIRED_INPUT_LEAVES)
    missing = sorted(required - found)
    extra = sorted(found - required)
    if missing or extra:
        raise SystemExit(
            "sealed inputs inventory drift missing=%s extra=%s" % (missing, extra)
        )


def main():
    _assert_required_leaves()
    sys.path.insert(0, BASE)
    import reference

    sealed = {}
    for name in _recording_directories(SEALED_INPUTS):
        sealed[name] = reference.expected(os.path.join(SEALED_INPUTS, name))
    with open(SEAL_PATH, "w", encoding="utf-8") as handle:
        json.dump(sealed, handle, indent=2, sort_keys=True)
        handle.write("\n")

    # Remove oracle import surface before graded pytest (R181 / AVA verifier_coverage).
    for victim in ("reference.py", "refpkg"):
        path = os.path.join(BASE, victim)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
    for key in list(sys.modules):
        if key == "reference" or key.startswith("refpkg"):
            del sys.modules[key]
    print("sealed", len(sealed), "ledgers at", SEAL_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
