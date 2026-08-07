# Off-policy pulse ledger

Harbor task: repair the asynchronous off-policy pulse ledger under
`task/environment/data/opulse` so every sealed recording pack emits a
contract-faithful ledger JSON at `/app/ledgers/<pack>.json`.

Category: Model Training and ML Infrastructure.
Subcategory: Reinforcement learning.
Agent-visible contract lives in `task/instruction.md` and `task/environment/data/spec/`.
Graded verifier and sealed expectations live under `task/tests/`.
