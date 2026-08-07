"""Return core using cut masks and segment boundaries."""

def compute_gae(rewards, next_v, next_nonterminal, values, gamma, lam, segments):
    T = len(rewards)
    adv = [0.0] * T
    ret = [0.0] * T
    gae = 0.0
    for t in reversed(range(T)):
        delta = rewards[t] + gamma * next_v[t] * next_nonterminal[t] - values[t]
        gae = delta + gamma * lam * next_nonterminal[t] * gae
        adv[t] = gae
        ret[t] = adv[t] + values[t]
    return adv, ret