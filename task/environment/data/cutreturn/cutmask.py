"""Build next-value and non-terminal masks for timeout-aware λ-returns."""

def build_cut_masks(terminated, truncated, values, bootstrap_value):
    """Seeded mask builder. Treats any cut-like flag as a hard episode end."""
    T = len(terminated)
    next_v = [0.0] * T
    next_nonterminal = [0.0] * T
    for t in range(T):
        # Seeded defect: timeout cuts and dual-flag rows are zeroed like terminations.
        if terminated[t] or truncated[t]:
            next_v[t] = 0.0
            next_nonterminal[t] = 0.0
        else:
            if t + 1 < T:
                next_v[t] = values[t + 1]
            else:
                next_v[t] = bootstrap_value
            next_nonterminal[t] = 1.0
    return next_v, next_nonterminal
