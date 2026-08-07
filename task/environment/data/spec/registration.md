# Critic registration (normative)

Trajectory rows store a raw `value` column. The recurrence must not use that column at the
same index. Meta key `value_lag` (integer >= 0) and `init_value` define the registered critic:

- For index `t >= value_lag`, `V_t = value[t - value_lag]`
- For index `t < value_lag`, `V_t = init_value`

Successor lookups that need a stored critic also use this registered series, not the raw
column. The registration helper is the only place that should apply lag.