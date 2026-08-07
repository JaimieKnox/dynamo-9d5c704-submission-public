"""Command line entry point: build one pulse ledger per recording pack."""

import argparse
import json
import os

from .learner import run_bundle


def pack_names(recordings_dir):
    return sorted(
        name
        for name in os.listdir(recordings_dir)
        if os.path.isfile(os.path.join(recordings_dir, name, "manifest.json"))
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Off-policy pulse ledger for asynchronous training recordings."
    )
    parser.add_argument("--recordings", default="/app/recordings")
    parser.add_argument("--out", default="/app/ledgers")
    parser.add_argument("--pack", action="append")
    args = parser.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    names = args.pack if args.pack else pack_names(args.recordings)
    for name in names:
        record = run_bundle(os.path.join(args.recordings, name))
        path = os.path.join(args.out, name + ".json")
        with open(path, "w") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print("wrote " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
