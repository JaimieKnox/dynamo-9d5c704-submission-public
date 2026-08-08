"""Reverse-time lambda returns with segment resets, scales, and eligibility cuts."""

def compute_gae(rewards, next_v, next_nonterminal, values, gamma, lam, segments, segment_scales, truncated=None):
    T = len(rewards)
    if truncated is None:
        truncated = [False] * T
    adv = [0.0] * T
    ret = [0.0] * T
    gae = 0.0
    for t in reversed(range(T)):
        if t + 1 < T and segments[t] != segments[t + 1]:
            gae = 0.0
        scale = float(segment_scales[segments[t]]) if segments[t] < len(segment_scales) else 1.0
        r = rewards[t] * scale
        delta = r + gamma * next_v[t] * next_nonterminal[t] - values[t]
        # Timeout keeps bootstrap inside delta, but eligibility does not carry through.
        elig = 0.0 if truncated[t] else float(next_nonterminal[t])
        gae = delta + gamma * lam * elig * gae
        adv[t] = gae
        ret[t] = adv[t] + values[t]
    return adv, ret
