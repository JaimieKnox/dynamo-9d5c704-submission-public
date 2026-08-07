"""Build next-value and non-terminal masks for timeout-aware λ-returns."""

def build_cut_masks(terminated, truncated, values, bootstrap_value):
    """Return (next_v, next_nonterminal) for each index.

    terminated wins when both flags are true.
    truncated (and not terminated) bootstraps from values[t+1] or bootstrap_value
    when t is the final horizon index. values has length T only.
    """
    T = len(terminated)
    next_v = [0.0] * T
    next_nonterminal = [0.0] * T
    for t in range(T):
        if terminated[t]:
            next_v[t] = 0.0
            next_nonterminal[t] = 0.0
        elif truncated[t]:
            if t + 1 < T:
                next_v[t] = values[t + 1]
            else:
                next_v[t] = bootstrap_value
            next_nonterminal[t] = 1.0
        else:
            if t + 1 < T:
                next_v[t] = values[t + 1]
            else:
                next_v[t] = bootstrap_value
            next_nonterminal[t] = 1.0
    return next_v, next_nonterminal
