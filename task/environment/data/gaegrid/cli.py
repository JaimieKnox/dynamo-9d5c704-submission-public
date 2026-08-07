"""CLI entrypoint."""
import argparse, json, os
from .ledger import run_pack

def pack_names(root):
    return sorted(n for n in os.listdir(root) if os.path.isfile(os.path.join(root, n, "meta.json")))

def main(argv=None):
    p = argparse.ArgumentParser(description="GAE truncation ledger")
    p.add_argument("--packs", default="/app/packs")
    p.add_argument("--out", default="/app/reports")
    p.add_argument("--pack", action="append")
    args = p.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    names = args.pack if args.pack else pack_names(args.packs)
    for name in names:
        doc = run_pack(os.path.join(args.packs, name))
        path = os.path.join(args.out, name + ".json")
        with open(path, "w") as fh:
            json.dump(doc, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print("wrote", path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
