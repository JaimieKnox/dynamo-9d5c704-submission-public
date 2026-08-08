"""Build reports from trajectory packs."""
import json, os
from .cutmask import build_cut_masks
from .gae import compute_gae
from .mass import advantage_mass_indices, fallback_mass_indices, return_mass_indices
from .pads import value_pad_mask
from .register import registered_stream
from .scale import scale_pad_mask
from .seam import segment_opens


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
    values = registered_stream(critic_a, lag_a, float(meta["init_a"]), segments)
    boot_values = registered_stream(critic_b, lag_b, float(meta["init_b"]), segments)
    scales = [float(x) for x in meta["segment_scales"]]
    scale_lag = int(meta.get("scale_lag", 0))
    resid_lag = int(meta.get("resid_lag", 0))
    gamma = float(meta["gamma"])
    gamma_lambda = float(meta["gamma_lambda"]) if "gamma_lambda" in meta else gamma
    segment_lambdas = None
    if "segment_lambdas" in meta:
        segment_lambdas = [float(x) for x in meta["segment_lambdas"]]
    next_v, next_nt, seam_edge = build_cut_masks(
        terminated, truncated, boot_values, float(meta.get("bootstrap_value", 0.0)),
        segments, raw_boot=critic_b, resid_lag=resid_lag,
    )
    adv, _ = compute_gae(
        rewards, next_v, next_nt, values, gamma, float(meta["lambda"]),
        segments, scales, truncated, scale_lag, seam_edge, gamma_lambda=gamma_lambda,
        lag_a=lag_a, segment_lambdas=segment_lambdas,
    )
    # Jump: reported return uses raw critic_a baseline, not registered values.
    ret = [adv[t] + critic_a[t] for t in range(len(adv))]
    T = len(rewards)
    lo = float(meta["is_clip_low"])
    hi = float(meta["is_clip_high"])
    power = float(meta.get("is_power", 1.0))
    opens = segment_opens(segments)
    open_w = {seg: float(weights[t0]) for seg, t0 in opens.items()}
    w_snap = [_clip((open_w[segments[t]] ** power), lo, hi) for t in range(T)]
    pads = scale_pad_mask(segments, scale_lag)
    vpads = value_pad_mask(segments, lag_a)
    idxs = advantage_mass_indices(terminated, seam_edge, pads, lag_b, segments, vpads)
    used_fallback = False
    if not idxs:
        used_fallback = True
        idxs = fallback_mass_indices(terminated, T)
    if used_fallback:
        clipped = [1.0] * len(idxs)
        denom = float(len(idxs))
    else:
        clipped = [w_snap[i] for i in idxs]
        denom = sum(clipped) or float(len(idxs))
        if denom <= 0:
            clipped = [1.0] * len(idxs)
            denom = float(len(idxs))
    mean_adv = sum(clipped[j] * adv[idxs[j]] for j in range(len(idxs))) / denom
    ret_idxs = return_mass_indices(terminated, pads, vpads)
    if not ret_idxs:
        ret_idxs = fallback_mass_indices(terminated, T)
    mean_ret = sum(ret[i] for i in ret_idxs) / float(len(ret_idxs))
    steps = [{
        "index": t,
        "advantage": _round6(adv[t]),
        "return": _round6(ret[t]),
        "bootstrapped": bool(truncated[t]) and not bool(terminated[t]),
    } for t in range(T)]
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
