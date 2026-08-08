"""Resolve successors from the bootstrap critic stream."""

def resolve_successor(
    t, horizon, terminated, truncated, boot_values, bootstrap_value, segments, seam_boots=None,
):
    if terminated[t]:
        return 0.0, 0.0
    if truncated[t]:
        return 0.0, 0.0
    if t + 1 >= horizon or (t + 1 < horizon and segments[t] != segments[t + 1]):
        return float(bootstrap_value), 1.0
    return float(boot_values[t + 1]), 1.0
