"""Pad membership for scale lags and value-register init fills."""

def value_pad_mask(segments, lag_a):
    T = len(segments)
    out = [False] * T
    if lag_a <= 0:
        return out
    for t in range(T):
        src = t - lag_a
        if src < 0 or segments[src] != segments[t]:
            out[t] = True
    return out
