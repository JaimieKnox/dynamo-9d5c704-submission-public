"""Independent reference implementation of the learner replay contract.

Written directly from /app/docs/learner-contract.md and deliberately structured
differently from the auditor under repair: admission indices come from the rank of a
transition in the globally sorted sequence, watermarks are resolved by bisection, epoch
evaluations are memoised tables, and the sampler stream is a generator. It shares no code
with the task environment.
"""

import bisect
import json
import math
import os

_M64 = (1 << 64) - 1
_GOLD = 0x9E3779B97F4A7C15


def _unit_stream(seed):
    state = seed & _M64
    while True:
        state = (state + _GOLD) & _M64
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _M64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _M64
        yield ((z ^ (z >> 31)) >> 11) * (2.0 ** -53)


def _read_json(path):
    with open(path) as handle:
        return json.load(handle)


def _read_lines(path):
    out = []
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def audit(bundle_dir):
    manifest = _read_json(os.path.join(bundle_dir, "manifest.json"))
    feats = _read_json(os.path.join(bundle_dir, "features.json"))
    admissions = _read_json(os.path.join(bundle_dir, "ingest.json"))["admissions"]

    pdir = os.path.join(bundle_dir, "params")
    epochs = [
        _read_json(os.path.join(pdir, name))
        for name in sorted(n for n in os.listdir(pdir) if n.endswith(".json"))
    ]

    value_memo = {}
    logp_memo = {}

    def value_of(epoch, obs_id):
        key = (epoch, obs_id)
        if key not in value_memo:
            snap = epochs[epoch]
            feat = feats[obs_id]
            value_memo[key] = snap["value_b"] + sum(
                w * x for w, x in zip(snap["value_w"], feat)
            )
        return value_memo[key]

    def logp_of(epoch, obs_id, action):
        key = (epoch, obs_id, action)
        if key not in logp_memo:
            snap = epochs[epoch]
            feat = feats[obs_id]
            logits = [
                bias + sum(w * x for w, x in zip(row, feat))
                for row, bias in zip(snap["policy_w"], snap["policy_b"])
            ]
            top = max(logits)
            logp_memo[key] = logits[action] - top - math.log(
                sum(math.exp(z - top) for z in logits)
            )
        return logp_memo[key]

    sdir = os.path.join(bundle_dir, "shards")
    rows = []
    for name in sorted(os.listdir(sdir)):
        if name.endswith(".jsonl"):
            rows.extend(_read_lines(os.path.join(sdir, name)))
    rows.sort(key=lambda row: row["seq"])
    seqs = [row["seq"] for row in rows]
    rank = {row["seq"]: index for index, row in enumerate(rows)}

    chains = {}
    for row in rows:
        chains.setdefault(row["episode_id"], []).append(row)
    for key in chains:
        chains[key].sort(key=lambda row: row["t"])

    capacity = manifest["buffer_capacity"]
    n_step = manifest["n_step"]
    gamma = manifest["gamma"]
    rho_bar = manifest["rho_bar"]
    c_bar = manifest["c_bar"]
    alpha = manifest["alpha"]
    beta = manifest["beta"]
    eps = manifest["priority_eps"]

    segments = []
    for episode_id in sorted(chains):
        chain = chains[episode_id]
        span = len(chain)
        for t0 in range(span):
            stop = None
            kind = None
            for j in range(t0, min(span, t0 + n_step)):
                if chain[j]["terminated"]:
                    stop, kind = j, "terminated"
                    break
                if chain[j]["truncated"]:
                    stop, kind = j, "truncated"
                    break
                if j - t0 + 1 == n_step:
                    stop, kind = j, "window"
                    break
            if kind is None:
                continue
            if kind == "terminated":
                boot = None
            elif kind == "truncated":
                boot = chain[stop]["cut_obs_id"]
            else:
                if stop + 1 >= span:
                    continue
                boot = chain[stop + 1]["obs_id"]
            member = chain[t0:stop + 1]
            indices = [rank[row["seq"]] for row in member]
            segments.append(
                {
                    "rows": member,
                    "kind": kind,
                    "boot": boot,
                    "start": indices[0],
                    "done": max(indices),
                    "position": None,
                }
            )

    def admitted_at(step):
        watermark = 0
        for entry in admissions:
            if entry["step"] <= step and entry["seq_watermark"] > watermark:
                watermark = entry["seq_watermark"]
        return bisect.bisect_right(seqs, watermark)

    ledger = []
    priority = []
    unregistered = list(segments)
    step_records = []
    draws_total = 0
    accepted_total = 0
    touched = set()
    admitted = 0

    for step in range(manifest["learner_steps"]):
        admitted = admitted_at(step)

        arriving = [seg for seg in unregistered if seg["done"] < admitted]
        if arriving:
            arriving.sort(key=lambda seg: (seg["done"], seg["start"]))
            waiting = [seg for seg in unregistered if seg["done"] >= admitted]
            for seg in arriving:
                seed_priority = None
                for pos, known in enumerate(ledger):
                    if admitted - known["start"] <= capacity:
                        if seed_priority is None or priority[pos] > seed_priority:
                            seed_priority = priority[pos]
                if seed_priority is None:
                    seed_priority = 1.0
                seg["position"] = len(ledger)
                ledger.append(seg)
                priority.append(seed_priority)
            unregistered = waiting

        size = len(ledger)
        epoch = min(step // manifest["target_refresh_interval"], len(epochs) - 1)
        total = sum(priority)

        sampled = []
        rejected = 0
        targets_pool = []
        advantage_pool = []
        raw_weights = []
        pending = {}

        if size > 0 and total > 0.0:
            stream = _unit_stream((manifest["sampler_seed"] ^ ((step * _GOLD) & _M64)) & _M64)
            for _ in range(manifest["batch_size"]):
                mark = next(stream) * total
                running = 0.0
                choice = size - 1
                for pos in range(size):
                    running += priority[pos]
                    if mark < running:
                        choice = pos
                        break
                draws_total += 1
                seg = ledger[choice]
                if admitted - seg["start"] > capacity:
                    rejected += 1
                    continue

                member = seg["rows"]
                span = len(member)
                values = [value_of(epoch, row["obs_id"]) for row in member]
                rhos = []
                cuts = []
                for row in member:
                    ratio = math.exp(
                        logp_of(epoch, row["obs_id"], row["action"]) - row["behavior_logp"]
                    )
                    rhos.append(rho_bar if ratio > rho_bar else ratio)
                    cuts.append(c_bar if ratio > c_bar else ratio)
                if seg["kind"] == "terminated":
                    boot = 0.0
                else:
                    boot = value_of(epoch, seg["boot"])

                raw = values + [boot]
                corrected = [0.0] * (span + 1)
                corrected[span] = boot
                for k in range(span - 1, -1, -1):
                    delta = rhos[k] * (member[k]["reward"] + gamma * raw[k + 1] - values[k])
                    corrected[k] = (
                        values[k] + delta + gamma * cuts[k] * (corrected[k + 1] - raw[k + 1])
                    )
                advantages = [
                    rhos[k] * (member[k]["reward"] + gamma * corrected[k + 1] - values[k])
                    for k in range(span)
                ]

                sampled.append(seg["start"] % capacity)
                targets_pool.extend(corrected[:span])
                advantage_pool.extend(advantages)
                raw_weights.append((size * (priority[choice] / total)) ** (-beta))
                pending[choice] = (
                    sum(abs(a) for a in advantages) / span + eps
                ) ** alpha
                accepted_total += 1
                touched.add(choice)

        if raw_weights:
            top = max(raw_weights)
            mean_weight = sum(w / top for w in raw_weights) / len(raw_weights)
        else:
            mean_weight = 0.0
        mean_target = sum(targets_pool) / len(targets_pool) if targets_pool else 0.0
        mean_advantage = (
            sum(advantage_pool) / len(advantage_pool) if advantage_pool else 0.0
        )

        for pos, new_priority in pending.items():
            priority[pos] = new_priority

        step_records.append(
            {
                "step": step,
                "target_epoch": epoch,
                "sampled": sampled,
                "dropped_nonresident": rejected,
                "mean_vtrace_target": round(mean_target, 6),
                "mean_pg_advantage": round(mean_advantage, 6),
                "mean_is_weight": round(mean_weight, 6),
                "priority_sum_after": round(sum(priority), 6),
            }
        )

    evicted = sum(1 for seg in ledger if admitted - seg["start"] > capacity)

    return {
        "bundle": manifest["bundle"],
        "steps": step_records,
        "totals": {
            "transitions_enqueued": admitted,
            "segments_registered": len(ledger),
            "segments_evicted": evicted,
            "draws": draws_total,
            "draws_accepted": accepted_total,
            "unique_segments_drawn": len(touched),
            "priority_sum_final": round(sum(priority), 6),
        },
    }
