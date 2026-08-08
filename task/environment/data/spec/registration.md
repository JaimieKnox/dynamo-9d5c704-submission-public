# Critic registration (normative)

Each trajectory row stores two raw critic columns: `critic_a` and `critic_b`.

Register a stream with lag `L` and fill `init` as:
- For index `t`, let `src = t - L`.
- If `src < 0`, registered[t] = init.
- If `src >= 0` and `segment[src] != segment[t]`, registered[t] = init (lag pads do not
  cross segment seams).
- Otherwise registered[t] = raw[src].

Use `lag_a` / `init_a` for the `critic_a` stream and `lag_b` / `init_b` for the `critic_b`
stream. Packs may choose different lags. Do not hardcode one lag for every trace.
