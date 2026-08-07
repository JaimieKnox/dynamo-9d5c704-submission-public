"""Build reports from trajectory packs."""
import json
import os
from .cutmask import build_cut_masks
from .gae import compute_gae

def _round6(x):
    return float(f"{x:.6f}")

def load_pack(pack_dir):
    with open(os.path.join(pack_dir, "meta.json")) as fh:
        meta = json.load(fh)
    rows = []
    with open(os.path.join(pack_dir, "trajectory.jsonl")) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    rows.sort(key=lambda r: r["index"])
    return meta, rows

def run_pack(pack_dir):
    meta, rows = load_pack(pack_dir)
    rewards = [float(r["reward"]) for r in rows]
    terminated = [bool(r["terminated"]) for r in rows]
    truncated = [bool(r["truncated"]) for r in rows]
    values = [float(r["value"]) for r in rows]
    bootstrap_value = float(meta["bootstrap_value"])
    gamma = float(meta["gamma"])
    lam = float(meta["lambda"])
    next_v, next_nonterminal = build_cut_masks(
        terminated, truncated, values, bootstrap_value
    )
    adv, ret = compute_gae(rewards, next_v, next_nonterminal, values, gamma, lam)
    # Seeded defect: full-horizon mean mass (no terminated exclusion / fallback).
    idxs = list(range(len(rewards)))
    mean_adv = sum(adv[i] for i in idxs) / len(idxs)
    mean_ret = sum(ret[i] for i in idxs) / len(idxs)
    steps = []
    for t in range(len(rewards)):
        steps.append({
            "index": t,
            "advantage": _round6(adv[t]),
            "return": _round6(ret[t]),
            # Seeded defect: marks dual-flag rows bootstrapped when truncated is set.
            "bootstrapped": bool(truncated[t]),
        })
    return {
        "pack": meta["pack"],
        "steps": steps,
        "summary": {
            "horizon": int(meta["horizon"]),
            "truncation_count": sum(1 for x in truncated if x),
            "termination_count": sum(1 for x in terminated if x),
            "mean_advantage": _round6(mean_adv),
            "mean_return": _round6(mean_ret),
        },
    }
