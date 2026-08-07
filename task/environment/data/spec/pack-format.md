# Pack format (normative)

Each directory under `/app/traces` contains:

- `meta.json` keys: `pack`, `gamma`, `lambda`, `bootstrap_value`, `horizon`, `value_lag`,
  `init_value`, `is_clip_low`, `is_clip_high`
- `trajectory.jsonl` keys: `index`, `reward`, `value`, `terminated`, `truncated`, `segment`,
  `is_weight`

Indices are contiguous from `0` to `horizon-1`.