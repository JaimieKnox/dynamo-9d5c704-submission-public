# Critic registration (normative)

Each trajectory row stores two raw critic columns: `critic_a` and `critic_b`.

Register a stream with lag `L` and fill `init` as:
- For index `t`, let `src = t - L`.
- If `src < 0`, registered[t] = init.
- If `src >= 0` and `segment[src] != segment[t]`, registered[t] = init.
- Otherwise registered[t] = raw[src].

Use `lag_a` / `init_a` for `critic_a` and `lag_b` / `init_b` for `critic_b`.
