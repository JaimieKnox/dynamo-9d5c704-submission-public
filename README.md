# Audit replay learner

Harbor task: repair the asynchronous actor-learner replay auditor under
`task/environment/data/rlaudit` so every sealed run bundle emits a contract-faithful
audit JSON at `/app/out/<bundle>.json`.

Category: Model Training and ML Infrastructure.
Agent-visible contract lives in `task/instruction.md` and `task/environment/data/docs/`.
Graded verifier and sealed expectations live under `task/tests/`.
