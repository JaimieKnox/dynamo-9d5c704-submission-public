"""λ-return core (fixed)."""

def compute_gae(rewards, values, terminated, truncated, gamma, lam):
    T = len(rewards)
    adv = [0.0] * T
    ret = [0.0] * T
    gae = 0.0
    for t in reversed(range(T)):
        if terminated[t]:
            next_v = 0.0
            next_nonterminal = 0.0
        else:
            next_v = values[t + 1]
            next_nonterminal = 1.0
        delta = rewards[t] + gamma * next_v * next_nonterminal - values[t]
        gae = delta + gamma * lam * next_nonterminal * gae
        adv[t] = gae
        ret[t] = adv[t] + values[t]
    return adv, ret
