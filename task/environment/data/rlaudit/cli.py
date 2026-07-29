"""Command line entry point: audit every run bundle and write one document per bundle."""

import argparse
import json
import os

from .learner import run_bundle


def bundle_names(runs_dir):
    return sorted(
        name
        for name in os.listdir(runs_dir)
        if os.path.isfile(os.path.join(runs_dir, name, "manifest.json"))
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Replay auditor for actor-learner run bundles.")
    parser.add_argument("--runs", default="/app/runs")
    parser.add_argument("--out", default="/app/out")
    parser.add_argument("--bundle", action="append")
    args = parser.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    names = args.bundle if args.bundle else bundle_names(args.runs)
    for name in names:
        record = run_bundle(os.path.join(args.runs, name))
        path = os.path.join(args.out, name + ".json")
        with open(path, "w") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print("wrote " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
