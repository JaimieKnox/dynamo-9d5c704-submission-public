"""Resolve per-index successor value and non-terminal multiplier."""

def resolve_successor(t, horizon, terminated, truncated, values, bootstrap_value, segments):
    if terminated[t]:
        return 0.0, 0.0
    if t + 1 < horizon:
        return float(values[t + 1]), 1.0
    return float(bootstrap_value), 1.0