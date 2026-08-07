"""Build cut masks via successor helper."""
from .successor import resolve_successor

def build_cut_masks(terminated, truncated, boot_values, bootstrap_value, segments):
    T = len(terminated)
    next_v = [0.0] * T
    next_nt = [0.0] * T
    for t in range(T):
        next_v[t], next_nt[t] = resolve_successor(
            t, T, terminated, truncated, boot_values, bootstrap_value, segments
        )
    return next_v, next_nt
