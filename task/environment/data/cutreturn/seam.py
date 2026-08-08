"""Segment-open freeze helpers shared by cut masks, successors, and the ledger."""

def segment_opens(segments):
    opens = {}
    for t, seg in enumerate(segments):
        if seg not in opens:
            opens[seg] = t
    return opens


def segment_lengths(segments):
    lengths = {}
    for seg in segments:
        lengths[seg] = lengths.get(seg, 0) + 1
    return lengths


def freeze_seam_bootstraps(boot_values, segments):
    opens = segment_opens(segments)
    return {seg: float(boot_values[t0]) for seg, t0 in opens.items()}


def is_seam_edge(t, horizon, segments):
    return (t + 1 >= horizon) or (segments[t] != segments[t + 1])


def open_used_cross_lag(t_open, lag_b, segments):
    if lag_b <= 0:
        return False
    src = t_open - lag_b
    if src < 0:
        return True
    return segments[src] != segments[t_open]
