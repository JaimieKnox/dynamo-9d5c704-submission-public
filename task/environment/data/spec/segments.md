# Segments and cut bootstraps (normative)

Termination: if `terminated[t]` then `V_next[t] = 0` and the successor non-terminal factor is 0.

Pure mid-segment truncation: when `truncated[t]` holds, the next index exists, and that next
index shares `segment[t]`, read raw `critic_b` at a residency index that walks back at most
`resid_lag` steps without leaving the segment. Non-terminal factor 1. This path is a
scale-through path.

Segment-edge / final index: when the next index is missing or belongs to another segment,
`V_next[t]` equals the registered bootstrap critic frozen at that segment's open index.
Non-terminal factor 1. This path is a scale-through path.

Interior continuation: otherwise `V_next[t]` equals the registered bootstrap critic at `t+1`,
non-terminal factor 1. This path is not scale-through.

Scale-through: before the TD residual uses `V_next[t]`, multiply it by the same effective
reward scale that multiplies `reward[t]` at that index (including `scale_lag` inheritance).
Interior continuation does not apply this extra multiply.

Reverse-time recurrence also zeros eligibility on truncation, open-freeze seam edges,
scale-lag pads, and value-pad indices from registration.md. Use the shared eligibility helper.
Zero the lambda accumulator immediately before updating an index that ends a segment.
