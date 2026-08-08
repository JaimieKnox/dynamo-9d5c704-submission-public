# Critic registration (normative)

Each row has raw `critic_a` and `critic_b`.

A registered stream of lag `L` and fill `init` must satisfy:
- registered[t] equals raw[t - L] when that source index exists and shares `segment[t]`
- registered[t] equals `init` when the source is missing or lies in a different segment

`critic_a` uses (`lag_a`, `init_a`). `critic_b` uses (`lag_b`, `init_b`). The reverse-time
state value is the registered `critic_a` stream. Bootstrap reads use registered `critic_b`.
