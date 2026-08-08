"""Resolve successors from bootstrap critics under cut invariants."""

def resolve_successor(
    t, horizon, terminated, truncated, boot_values, bootstrap_value, segments,
    seam_boots=None, raw_boot=None, resid_lag=0,
):
    if terminated[t]:
        return 0.0, 0.0
    if truncated[t] and t + 1 < horizon and segments[t] == segments[t + 1]:
        src = raw_boot if raw_boot is not None else boot_values
        open_t = t
        while open_t > 0 and segments[open_t - 1] == segments[t]:
            open_t -= 1
        src_t = t - int(resid_lag)
        if src_t < open_t:
            src_t = open_t
        return float(src[src_t]), 1.0
    if t + 1 >= horizon or segments[t] != segments[t + 1]:
        if seam_boots is not None:
            return float(seam_boots[segments[t]]), 1.0
        return float(bootstrap_value), 1.0
    return float(boot_values[t + 1]), 1.0
