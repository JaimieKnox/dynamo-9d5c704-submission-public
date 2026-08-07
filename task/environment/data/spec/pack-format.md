# Pack format (normative)

Each pack directory under `/app/traces` has `meta.json` and `trajectory.jsonl`.

`meta.json` keys: `pack`, `gamma`, `lambda`, `bootstrap_value`, `horizon`, `lag_a`, `lag_b`,
`init_a`, `init_b`, `segment_scales` (array of floats, one per segment id), `is_clip_low`,
`is_clip_high`, `is_power`.

`trajectory.jsonl` keys: `index`, `reward`, `critic_a`, `critic_b`, `terminated`, `truncated`,
`segment`, `is_weight`.

## Streams

The reverse-time state value at index `t` is the lag-`lag_a` registration of `critic_a`
(with fill `init_a`). Successor bootstraps that need a critic read the lag-`lag_b`
registration of `critic_b` (with fill `init_b`). Do not use one stream for both roles.

## Composition

Timeout residency, segment edges, reward scales, eligibility cuts, and mass algebra are
specified across `segments.md`, `registration.md`, `weighting.md`, and `contract.md`. Every
rule applies together on mixed packs.
