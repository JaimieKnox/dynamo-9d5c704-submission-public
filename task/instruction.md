The package at `/app/opulse` rebuilds an offline importance-corrected pulse ledger
from asynchronous actor shards. The tree runs end to end, but graded ledgers diverge
when residency across a formed segment's covered admissions, truncated-cut bootstrap
choice, importance mass under sampler lag, and publication-quarantine eligibility
interact on the same learner ticks. Repair the implementation so those interactions
match the specification.

Each directory under `/app/recordings` is one recording pack.
`/app/spec/recording-format.md`, `/app/spec/pulse-contract.md`,
`/app/spec/decision-tables.md`, `/app/spec/draw-engine.md`, and
`/app/spec/ledger-schema.md` are normative and together state every rule that decides
a pulse ledger.

Write one pulse ledger per pack to `/app/ledgers/<pack>.json`, using the pack
directory name. For every pack under `/app/recordings`:

1. The ledger exists, parses as JSON, and carries `recording`, `ticks`, and `summary`.
2. `ticks` has one correctly typed entry per learner tick in ascending order.
3. `active_epoch` is the reported epoch in force for that tick.
4. `accepted_slots` is the exact ordered slot sequence of accepted draws, repeats included.
5. `rejected_count` is the exact rejected-draw count.
6. The four per-tick floating aggregates match the contract to six decimal places.
7. `summary` contains the six exact counts and rounded final priority mass.

No pack ships an expected ledger. Only `/app/ledgers` is graded. You may replace
anything under `/app/opulse`.
