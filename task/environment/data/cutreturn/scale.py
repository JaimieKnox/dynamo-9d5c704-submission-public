"""Effective segment scales and scale-lag pad membership."""

def segment_opens(segments):
    opens = {}
    for t, seg in enumerate(segments):
        if seg not in opens:
            opens[seg] = t
    return opens


def in_scale_pad(t, segments, scale_lag):
    """True when index t inherits the previous segment's scale (scale_lag pad)."""
    if scale_lag <= 0:
        return False
    opens = segment_opens(segments)
    seg = segments[t]
    t_open = opens[seg]
    if t_open <= 0:
        return False
    return (t - t_open) < scale_lag


def effective_scale(t, segments, segment_scales, scale_lag):
    opens = segment_opens(segments)
    seg = segments[t]
    t_open = opens[seg]
    if scale_lag > 0 and (t - t_open) < scale_lag and t_open > 0:
        prev_seg = segments[t_open - 1]
        if prev_seg < len(segment_scales):
            return float(segment_scales[prev_seg])
        return 1.0
    if seg < len(segment_scales):
        return float(segment_scales[seg])
    return 1.0


def scale_pad_mask(segments, scale_lag):
    return [in_scale_pad(t, segments, scale_lag) for t in range(len(segments))]
