"""Reconcile produced audit documents against expected.json for sample bundles."""

import json
import os
import sys


def main(argv=None):
    runs = "/app/runs"
    out = "/app/out"
    names = sorted(
        name
        for name in os.listdir(runs)
        if os.path.isfile(os.path.join(runs, name, "expected.json"))
    )
    if not names:
        print("no sample bundles with expected.json")
        return 1
    failed = 0
    for name in names:
        got_path = os.path.join(out, name + ".json")
        exp_path = os.path.join(runs, name, "expected.json")
        if not os.path.isfile(got_path):
            print(name + ": missing " + got_path)
            failed += 1
            continue
        with open(got_path) as handle:
            got = json.load(handle)
        with open(exp_path) as handle:
            exp = json.load(handle)
        if got == exp:
            print(name + ": ok")
        else:
            print(name + ": differs from expected.json")
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
