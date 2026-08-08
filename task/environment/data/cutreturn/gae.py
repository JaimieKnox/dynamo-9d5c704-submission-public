"""Reverse-time lambda returns with segment resets, open scale pads, and truncation cuts."""

def compute_gae(
    rewards, next_v, next_nonterminal, values, gamma, lam, segments, segment_scales,
    truncated=None, scale_lag=0, seam_edge=None,
):
    T = len(rewards)
    if truncated is None:
        truncated = [False] * T
    opens = {}
    for t, seg in enumerate(segments):
        if seg not in opens:
            opens[seg] = t
    adv = [0.0] * T
    ret = [0.0] * T
    gae = 0.0
    for t in reversed(range(T)):
        if t + 1 < T and segments[t] != segments[t + 1]:
            gae = 0.0
        seg = segments[t]
        t_open = opens[seg]
        if scale_lag > 0 and (t - t_open) < scale_lag and t_open > 0:
            prev_seg = segments[t_open - 1]
            scale = float(segment_scales[prev_seg]) if prev_seg < len(segment_scales) else 1.0
        else:
            scale = float(segment_scales[seg]) if seg < len(segment_scales) else 1.0
        r = rewards[t] * scale
        delta = r + gamma * next_v[t] * next_nonterminal[t] - values[t]
        elig = 0.0 if truncated[t] else float(next_nonterminal[t])
        gae = delta + gamma * lam * elig * gae
        adv[t] = gae
        ret[t] = adv[t] + values[t]
    return adv, ret
