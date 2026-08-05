"""Phase A: seal oracle ledgers, then remove the reference tree before pytest."""

from __future__ import annotations

import json
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SEALED_INPUTS = os.path.join(BASE, "inputs")
SEAL_PATH = os.path.join(BASE, "sealed_expectations.json")


def _recording_directories(parent):
    names = []
    for candidate in os.listdir(parent):
        marker = os.path.join(parent, candidate, "manifest.json")
        if os.path.isfile(marker):
            names.append(candidate)
    return sorted(names)


def main():
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
