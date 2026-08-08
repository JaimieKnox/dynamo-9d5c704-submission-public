# Segments and cut bootstraps (normative)

Each row has integer `segment`.

1. Reverse-time lambda accumulator resets to zero when `segment[t] != segment[t+1]` before
   updating index `t`.
2. At each segment open index, freeze the already-registered `critic_b` stream value for that
   segment. A segment may contain only one index.
3. For non-terminated rows, if `t` is final or `segment[t] != segment[t+1]`, successor value is
   that segment's open freeze, with non-terminal multiplier one. This includes single-index
   segments, which are open and edge at the same index.
4. For non-terminated pure truncation that continues inside a multi-index segment
   (`truncated=true`, next index exists, same segment), successor value is the registered
   `critic_b` stream at the same index `t` (not `t+1`), with non-terminal multiplier one.
5. For non-terminated rows continuing inside a segment without truncation, successor value is
   the registered `critic_b` stream at `t+1`.
6. `terminated=true` zeros successor value and non-terminal multiplier even when `truncated`
   is also true.
7. Before the TD residual, multiply `reward[t]` by `segment_scales[segment[t]]`.
8. After the TD residual, reverse-time eligibility uses non-terminal multiplier zero on
   truncated rows. The timeout bootstrap remains inside the residual; lambda eligibility does
   not carry through the cut.
9. Record a seam-edge mask bit for every non-terminated index that used rule (3). Summary mass
   rules in `weighting.md` consume that mask.
