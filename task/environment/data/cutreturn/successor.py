"""Resolve successors from the bootstrap critic stream."""

def resolve_successor(t, horizon, terminated, truncated, boot_values, bootstrap_value, segments):
    if terminated[t] or truncated[t]:
        return 0.0, 0.0
    if t + 1 < horizon:
        return float(boot_values[t + 1]), 1.0
    return 0.0, 0.0
