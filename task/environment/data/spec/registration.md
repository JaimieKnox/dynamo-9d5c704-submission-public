# Critic registration (normative)

Each trajectory row stores two raw critic columns: `critic_a` and `critic_b`.

Register a stream with lag `L` and fill `init` as:
- For index `t >= L`, registered[t] = raw[t - L]
- For index `t < L`, registered[t] = init

Use `lag_a` / `init_a` for the `critic_a` stream and `lag_b` / `init_b` for the `critic_b`
stream. Packs may choose different lags. Do not hardcode one lag for every trace.
