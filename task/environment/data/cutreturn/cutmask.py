"""Build cut masks via successor helper and segment-open freezes."""
from .seam import freeze_seam_bootstraps, is_seam_edge
from .successor import resolve_successor


def build_cut_masks(
    terminated, truncated, boot_values, bootstrap_value, segments,
    raw_boot=None, resid_lag=0,
):
    T = len(terminated)
    seam_boots = freeze_seam_bootstraps(boot_values, segments)
    next_v = [0.0] * T
    next_nt = [0.0] * T
    seam_edge = [False] * T
    for t in range(T):
        seam_edge[t] = (not terminated[t]) and is_seam_edge(t, T, segments)
        next_v[t], next_nt[t] = resolve_successor(
            t, T, terminated, truncated, boot_values, bootstrap_value, segments,
            seam_boots=seam_boots, raw_boot=raw_boot, resid_lag=resid_lag,
        )
    return next_v, next_nt, seam_edge
