"""Segment-open freeze helpers shared by cut masks, successors, and the ledger."""

def segment_opens(segments):
    opens = {}
    for t, seg in enumerate(segments):
        if seg not in opens:
            opens[seg] = t
    return opens


def freeze_seam_bootstraps(boot_values, segments):
    """Freeze registered bootstrap-stream values at each segment open index."""
    opens = segment_opens(segments)
    return {seg: float(boot_values[t0]) for seg, t0 in opens.items()}


def is_seam_edge(t, horizon, segments):
    return (t + 1 >= horizon) or (segments[t] != segments[t + 1])


def open_used_cross_lag(t_open, lag_b, segments):
    """True when the lag-b source for a segment-open freeze crosses a seam or pad."""
    if lag_b <= 0:
        return False
    src = t_open - lag_b
    if src < 0:
        return True
    return segments[src] != segments[t_open]


def seam_bootstrap_excluded(t, horizon, segments, lag_b):
    """Rows whose seam-edge bootstrap used a cross-lag open freeze leave the IS pool."""
    if not is_seam_edge(t, horizon, segments):
        return False
    opens = segment_opens(segments)
    t_open = opens[segments[t]]
    return open_used_cross_lag(t_open, lag_b, segments)
