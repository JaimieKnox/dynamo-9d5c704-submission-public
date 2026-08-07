"""Resolve per-index successor value and non-terminal multiplier."""

def resolve_successor(t, horizon, terminated, truncated, values, bootstrap_value):
    if terminated[t] and not truncated[t]:
        return 0.0, 0.0
    if truncated[t] and t + 1 < horizon:
        return float(values[t]), 1.0
    if truncated[t]:
        return 0.0, 1.0
    if t + 1 < horizon:
        return float(values[t + 1]), 1.0
    return float(bootstrap_value), 1.0
