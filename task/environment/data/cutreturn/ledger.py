"""Build reports from trajectory packs."""
import json, os
from .cutmask import build_cut_masks
from .gae import compute_gae
from .register import registered_stream

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
    critic_a = [float(r["critic_a"]) for r in rows]
    segments = [int(r["segment"]) for r in rows]
    weights = [float(r["is_weight"]) for r in rows]
    values = registered_stream(critic_a, int(meta["lag_a"]), float(meta["init_a"]))
    boot_values = values
    scales = [float(x) for x in meta["segment_scales"]]
    next_v, next_nt = build_cut_masks(
        terminated, truncated, boot_values, float(meta["bootstrap_value"]), segments
    )
    adv, ret = compute_gae(
        rewards, next_v, next_nt, values, float(meta["gamma"]), float(meta["lambda"]),
        segments, scales, truncated,
    )
    idxs = list(range(len(rewards)))
    mean_adv = sum(weights[i] * adv[i] for i in idxs) / sum(weights[i] for i in idxs)
    mean_ret = sum(weights[i] * ret[i] for i in idxs) / sum(weights[i] for i in idxs)
    steps = [{
        "index": t,
        "advantage": _round6(adv[t]),
        "return": _round6(ret[t]),
        "bootstrapped": bool(truncated[t]),
    } for t in range(len(rewards))]
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
