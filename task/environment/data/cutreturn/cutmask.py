"""Build next-value and non-terminal masks for timeout-aware returns."""
from .successor import resolve_successor

def build_cut_masks(terminated, truncated, registered, raw_values, bootstrap_value, segments):
    T = len(terminated)
    next_v = [0.0] * T
    next_nonterminal = [0.0] * T
    for t in range(T):
        next_v[t], next_nonterminal[t] = resolve_successor(
            t, T, terminated, truncated, registered, raw_values, bootstrap_value, segments
        )
    return next_v, next_nonterminal