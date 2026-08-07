# Pack format (normative)

Each pack directory under `/app/traces` has `meta.json` and `trajectory.jsonl`.

`meta.json` keys: `pack`, `gamma`, `lambda`, `bootstrap_value`, `horizon`, `lag_a`, `lag_b`,
`init_a`, `init_b`, `segment_scales` (array of floats, one per segment id), `is_clip_low`,
`is_clip_high`.

`trajectory.jsonl` keys: `index`, `reward`, `critic_a`, `critic_b`, `terminated`, `truncated`,
`segment`, `is_weight`.

## Streams

The reverse-time state value at index `t` is the lag-`lag_a` registration of `critic_a`
(with fill `init_a`). Successor bootstraps that need a next critic read the lag-`lag_b`
registration of `critic_b` (with fill `init_b`). Do not use one stream for both roles.

## Edges

For non-terminated rows, if `t` is final or `segment[t] != segment[t+1]`, successor value is
`bootstrap_value` with non-terminal multiplier one. Otherwise successor value is the
registered `critic_b` stream at `t+1`. Termination zeros both successor channels even when
`truncated` is also true.

## Rewards and mass

Before the TD residual, multiply `reward[t]` by `segment_scales[segment[t]]`. Summary means
average over non-terminated indices (truncated stays in). Clip each mass weight into
`[is_clip_low, is_clip_high]`, renormalize clipped weights to sum to one over the mass set,
then average. If every index is terminated, use the full horizon with the same rule.
