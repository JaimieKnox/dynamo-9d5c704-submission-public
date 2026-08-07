"""Resolve per-index successor value and non-terminal multiplier."""

def resolve_successor(t, horizon, terminated, truncated, registered, raw_values, bootstrap_value, segments):
    if terminated[t]:
        return 0.0, 0.0
    if truncated[t]:
        cross = (t + 1 >= horizon) or (segments[t] != segments[t + 1])
        if cross:
            return float(bootstrap_value), 1.0
        return float(registered[t + 1]), 1.0
    if t + 1 < horizon and segments[t] == segments[t + 1]:
        return float(registered[t + 1]), 1.0
    return float(bootstrap_value), 1.0