# Pack format (normative)

Each directory under `/app/traces` contains:

- `meta.json` with keys `pack`, `gamma`, `lambda`, `bootstrap_value`, `horizon`
- `trajectory.jsonl` with one object per index and keys `index`, `reward`, `value`,
  `terminated`, `truncated`, `segment`, `is_weight`

Indices are contiguous from `0` to `horizon-1`.
