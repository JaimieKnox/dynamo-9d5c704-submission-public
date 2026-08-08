"""Shared reverse-time eligibility factors."""

def eligibility_factor(t, truncated, seam_edge, scale_pad, value_pad, next_nonterminal):
    if truncated[t] or seam_edge[t] or scale_pad[t] or value_pad[t]:
        return 0.0
    return float(next_nonterminal[t])
