"""Phase A: seal oracle ledgers, remove reference tree."""
from __future__ import annotations
import json, os, shutil, sys
BASE = os.path.dirname(os.path.abspath(__file__))
SEALED_INPUTS = os.path.join(BASE, "inputs")
SEAL_PATH = os.path.join(BASE, "sealed_expectations.json")
REQUIRED_INPUT_LEAVES = []
for root, dirs, files in os.walk(SEALED_INPUTS):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), SEALED_INPUTS).replace("\\", "/")
        REQUIRED_INPUT_LEAVES.append(rel)
REQUIRED_INPUT_LEAVES.sort()

def main():
    missing = [p for p in REQUIRED_INPUT_LEAVES if not os.path.isfile(os.path.join(SEALED_INPUTS, p))]
    if missing:
        raise SystemExit("missing input leaves: %s" % missing)
    sys.path.insert(0, BASE)
    from refpkg.ledger import run_pack
    sealed = {}
    for name in sorted(os.listdir(SEALED_INPUTS)):
        d = os.path.join(SEALED_INPUTS, name)
        if os.path.isfile(os.path.join(d, "meta.json")):
            sealed[name] = run_pack(d)
    with open(SEAL_PATH, "w") as fh:
        json.dump(sealed, fh, indent=2, sort_keys=True)
        fh.write("\n")
    shutil.rmtree(os.path.join(BASE, "refpkg"), ignore_errors=True)
    p = os.path.join(BASE, "reference.py")
    if os.path.isfile(p):
        os.remove(p)
    print("sealed", len(sealed), "packs")

if __name__ == "__main__":
    main()
