"""Reverse-time lambda returns with dual discount, scale pads, and eligibility cuts."""
from .scale import effective_scale, scale_pad_mask


def compute_gae(
    rewards, next_v, next_nonterminal, values, gamma, lam, segments, segment_scales,
    truncated=None, scale_lag=0, seam_edge=None, gamma_lambda=None,
):
    T = len(rewards)
    if truncated is None:
        truncated = [False] * T
    if seam_edge is None:
        seam_edge = [False] * T
    if gamma_lambda is None:
        gamma_lambda = gamma
    pads = scale_pad_mask(segments, scale_lag)
    adv = [0.0] * T
    ret = [0.0] * T
    gae = 0.0
    for t in reversed(range(T)):
        if t + 1 < T and segments[t] != segments[t + 1]:
            gae = 0.0
        scale = effective_scale(t, segments, segment_scales, scale_lag)
        r = rewards[t] * scale
        delta = r + gamma * next_v[t] * next_nonterminal[t] - values[t]
        if truncated[t] or seam_edge[t] or pads[t]:
            elig = 0.0
        else:
            elig = float(next_nonterminal[t])
        gae = delta + gamma_lambda * lam * elig * gae
        adv[t] = gae
        ret[t] = adv[t] + values[t]
    return adv, ret
