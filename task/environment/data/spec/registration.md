# Critic registration (normative)

Trajectory rows store a raw `value` column. Baseline critics in the recurrence use a
registered series defined by meta `value_lag` and `init_value`:

- For index `t >= value_lag`, `V_t = value[t - value_lag]`
- For index `t < value_lag`, `V_t = init_value`

`value_lag` may differ across packs. Do not hardcode a single lag for every trace.

Successor selection is not uniformly lagged. See `segments.md` for which successor path
reads the raw column versus the registered series versus `bootstrap_value`.