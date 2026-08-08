"""Pad membership for scale lags and value-register init fills."""

def segment_opens(segments):
    opens = {}
    for t, seg in enumerate(segments):
        if seg not in opens:
            opens[seg] = t
    return opens


def value_pad_mask(segments, lag_a):
    """True when registered critic_a at t would read init (missing or cross-seam)."""
    T = len(segments)
    out = [False] * T
    if lag_a <= 0:
        return out
    for t in range(T):
        src = t - lag_a
        if src < 0 or segments[src] != segments[t]:
            out[t] = True
    return out
