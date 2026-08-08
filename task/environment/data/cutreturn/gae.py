"""Reverse-time lambda returns with dual discount and shared eligibility."""
from .elig import eligibility_factor
from .pads import value_pad_mask
from .scale import effective_scale, scale_pad_mask


def compute_gae(
    rewards, next_v, next_nonterminal, values, gamma, lam, segments, segment_scales,
    truncated=None, scale_lag=0, seam_edge=None, gamma_lambda=None, lag_a=0,
    segment_lambdas=None,
):
    T = len(rewards)
    if truncated is None:
        truncated = [False] * T
    if seam_edge is None:
        seam_edge = [False] * T
    if gamma_lambda is None:
        gamma_lambda = gamma
    pads = scale_pad_mask(segments, scale_lag)
    vpads = value_pad_mask(segments, lag_a)
    adv = [0.0] * T
    ret_acc = [0.0] * T
    gae = 0.0
    for t in reversed(range(T)):
        if t + 1 < T and segments[t] != segments[t + 1]:
            gae = 0.0
        scale = effective_scale(t, segments, segment_scales, scale_lag)
        r = rewards[t] * scale
        delta = r + gamma * next_v[t] * next_nonterminal[t] - values[t]
        elig = eligibility_factor(t, truncated, seam_edge, pads, vpads, next_nonterminal)
        lam_t = float(lam)
        if segment_lambdas is not None:
            seg = segments[t]
            if seg < len(segment_lambdas):
                lam_t = float(segment_lambdas[seg])
        gae = delta + gamma_lambda * lam_t * elig * gae
        adv[t] = gae
        ret_acc[t] = gae
    return adv, ret_acc
