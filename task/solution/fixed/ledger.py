"""Build reports from trajectory packs."""
import json
import os

from .cutmask import build_cut_masks
from .gae import compute_gae
from .register import registered_stream
from .seam import open_used_cross_lag, segment_opens


def _round6(x):
    return float(f"{x:.6f}")


def _clip(w, lo, hi):
    return lo if w < lo else hi if w > hi else w


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
    critic_b = [float(r["critic_b"]) for r in rows]
    segments = [int(r["segment"]) for r in rows]
    weights = [float(r["is_weight"]) for r in rows]
    lag_a = int(meta["lag_a"])
    lag_b = int(meta["lag_b"])
    init_a = float(meta["init_a"])
    init_b = float(meta["init_b"])
    values = registered_stream(critic_a, lag_a, init_a, segments)
    boot_values = registered_stream(critic_b, lag_b, init_b, segments)
    scales = [float(x) for x in meta["segment_scales"]]
    next_v, next_nt, seam_edge = build_cut_masks(
        terminated, truncated, boot_values, float(meta.get("bootstrap_value", 0.0)), segments
    )
    adv, ret = compute_gae(
        rewards,
        next_v,
        next_nt,
        values,
        float(meta["gamma"]),
        float(meta["lambda"]),
        segments,
        scales,
    )
    T = len(rewards)
    lo = float(meta["is_clip_low"])
    hi = float(meta["is_clip_high"])
    w_snap = [_clip(weights[t], lo, hi) for t in range(T)]
    opens = segment_opens(segments)
    idxs = []
    for i in range(T):
        if terminated[i]:
            continue
        if seam_edge[i]:
            t_open = opens[segments[i]]
            if open_used_cross_lag(t_open, lag_b, segments):
                continue
        idxs.append(i)
    if not idxs:
        idxs = [i for i in range(T) if not terminated[i]]
    if not idxs:
        idxs = list(range(T))
    clipped = [w_snap[i] for i in idxs]
    denom = sum(clipped)
    if denom <= 0:
        clipped = [1.0] * len(idxs)
        denom = float(len(idxs))
    mean_adv = sum(clipped[j] * adv[idxs[j]] for j in range(len(idxs))) / denom
    mean_ret = sum(clipped[j] * ret[idxs[j]] for j in range(len(idxs))) / denom
    steps = [
        {
            "index": t,
            "advantage": _round6(adv[t]),
            "return": _round6(ret[t]),
            "bootstrapped": bool(truncated[t]) and not bool(terminated[t]),
        }
        for t in range(T)
    ]
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
