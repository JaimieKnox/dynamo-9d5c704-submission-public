"""Independent reference implementation of the learner replay contract.

Written directly from /app/docs/learner-contract.md, /app/docs/defect-modes.md and
/app/docs/output-schema.md, and deliberately structured differently from the auditor under
repair: admission indices are assigned by walking an explicit per step admission plan,
watermarks are folded ahead of the replay, epoch evaluations are memoised tables, the sampler
stream is a generator, and segments are plain dicts keyed on their member admission indices.
It shares no code with the task environment.
"""

import hashlib
import json
import math
import os

_M64 = (1 << 64) - 1
_GOLD = 0x9E3779B97F4A7C15

# Candidate order of /app/docs/defect-modes.md.
MODES = (
    "none",
    "shard_local_order",
    "watermark_last_entry",
    "residency_by_last_transition",
    "truncated_bootstrap_acting_obs",
    "seed_constant_one",
    "weight_norm_over_all_draws",
)


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


def _micros(value):
    return int(round(value * 1000000))


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def step_digest(record):
    """Digest of one step ledger entry, per /app/docs/output-schema.md."""
    fields = [
        str(int(record["step"])),
        str(int(record["target_epoch"])),
        ",".join(str(int(slot)) for slot in record["sampled"]),
        str(int(record["dropped_nonresident"])),
        str(_micros(record["mean_vtrace_target"])),
        str(_micros(record["mean_pg_advantage"])),
        str(_micros(record["mean_is_weight"])),
        str(_micros(record["priority_sum_after"])),
    ]
    return _digest("|".join(fields))


def totals_digest(totals):
    """Digest of the run totals object, per /app/docs/output-schema.md."""
    fields = [
        str(int(totals["transitions_enqueued"])),
        str(int(totals["segments_registered"])),
        str(int(totals["segments_evicted"])),
        str(int(totals["draws"])),
        str(int(totals["draws_accepted"])),
        str(int(totals["unique_segments_drawn"])),
        str(_micros(totals["priority_sum_final"])),
    ]
    return _digest("|".join(fields))


def ledger_digests(document):
    return {
        "step_digests": [step_digest(record) for record in document["steps"]],
        "totals_digest": totals_digest(document["totals"]),
    }


def _visible_marks(admissions, steps, mode):
    """Highest sequence number in force at each learner step."""
    marks = []
    for step in range(steps):
        mark = 0
        if mode == "watermark_last_entry":
            for entry in admissions:
                if entry["step"] <= step:
                    mark = entry["seq_watermark"]
        else:
            for entry in admissions:
                if entry["step"] <= step and entry["seq_watermark"] > mark:
                    mark = entry["seq_watermark"]
        marks.append(mark)
    return marks


def _admission_plan(rows, marks, mode):
    """Admission index of every transition ever admitted, and the count held per step."""
    if mode == "shard_local_order":
        order = sorted(rows, key=lambda row: (row["actor_id"], row["seq"]))
    else:
        order = sorted(rows, key=lambda row: row["seq"])

    index_of = {}
    per_step = []
    reach = 0
    waiting = order
    for mark in marks:
        if mark > reach:
            reach = mark
        held_back = []
        for row in waiting:
            if row["seq"] <= reach:
                index_of[row["seq"]] = len(index_of)
            else:
                held_back.append(row)
        waiting = held_back
        per_step.append(len(index_of))
    return index_of, per_step


def audit(bundle_dir, mode="none"):
    """Replay one bundle under the contract, or under one documented deviation."""
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

    steps_count = manifest["learner_steps"]
    marks = _visible_marks(admissions, steps_count, mode)
    index_of, held_per_step = _admission_plan(rows, marks, mode)

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
                if mode == "truncated_bootstrap_acting_obs":
                    boot = chain[stop]["obs_id"]
                else:
                    boot = chain[stop]["cut_obs_id"]
            else:
                if stop + 1 >= span:
                    continue
                boot = chain[stop + 1]["obs_id"]
            member = chain[t0:stop + 1]
            if any(row["seq"] not in index_of for row in member):
                continue
            indices = [index_of[row["seq"]] for row in member]
            segments.append(
                {
                    "rows": member,
                    "kind": kind,
                    "boot": boot,
                    "first": indices[0],
                    "last": indices[-1],
                    "earliest": min(indices),
                    "latest": max(indices),
                }
            )

    ledger = []
    priority = []
    unregistered = list(segments)
    step_records = []
    draws_total = 0
    accepted_total = 0
    touched = set()
    held = 0

    def anchor(seg):
        if mode == "residency_by_last_transition":
            return seg["latest"]
        return seg["earliest"]

    for step in range(steps_count):
        held = held_per_step[step]

        arriving = [seg for seg in unregistered if seg["latest"] < held]
        if arriving:
            arriving.sort(key=lambda seg: (seg["last"], seg["first"]))
            unregistered = [seg for seg in unregistered if seg["latest"] >= held]
            for seg in arriving:
                if mode == "seed_constant_one":
                    seed = 1.0
                else:
                    seed = max(priority) if priority else 1.0
                ledger.append(seg)
                priority.append(seed)

        size = len(ledger)
        epoch = min(step // manifest["target_refresh_interval"], len(epochs) - 1)
        total = sum(priority)

        sampled = []
        rejected = 0
        targets_pool = []
        advantage_pool = []
        accepted_weights = []
        every_weight = []
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
                raw_weight = (size * (priority[choice] / total)) ** (-beta)
                every_weight.append(raw_weight)
                if held - anchor(seg) > capacity:
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

                sampled.append(seg["first"] % capacity)
                targets_pool.extend(corrected[:span])
                advantage_pool.extend(advantages)
                accepted_weights.append(raw_weight)
                pending[choice] = (
                    sum(abs(a) for a in advantages) / span + eps
                ) ** alpha
                accepted_total += 1
                touched.add(choice)

        if accepted_weights:
            if mode == "weight_norm_over_all_draws":
                top = max(every_weight)
            else:
                top = max(accepted_weights)
            mean_weight = sum(w / top for w in accepted_weights) / len(accepted_weights)
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

    evicted = sum(1 for seg in ledger if held - anchor(seg) > capacity)

    return {
        "bundle": manifest["bundle"],
        "steps": step_records,
        "totals": {
            "transitions_enqueued": held,
            "segments_registered": len(ledger),
            "segments_evicted": evicted,
            "draws": draws_total,
            "draws_accepted": accepted_total,
            "unique_segments_drawn": len(touched),
            "priority_sum_final": round(sum(priority), 6),
        },
    }


def diagnosis(bundle_dir, faithful=None):
    """The diagnosis object /app/docs/defect-modes.md selects for one bundle."""
    recorded = _read_json(os.path.join(bundle_dir, "production", "ledger-digest.json"))
    if faithful is None:
        faithful = audit(bundle_dir, "none")
    produced = ledger_digests(faithful)

    first_divergent = -1
    for index, digest in enumerate(produced["step_digests"]):
        recorded_steps = recorded["step_digests"]
        if index >= len(recorded_steps) or digest != recorded_steps[index]:
            first_divergent = index
            break

    defect = None
    for mode in MODES:
        candidate = produced if mode == "none" else ledger_digests(audit(bundle_dir, mode))
        if (
            candidate["step_digests"] == recorded["step_digests"]
            and candidate["totals_digest"] == recorded["totals_digest"]
        ):
            defect = mode
            break

    return {"first_divergent_step": first_divergent, "defect": defect}


def expected(bundle_dir):
    """The full audit document the contract produces for one bundle."""
    document = audit(bundle_dir, "none")
    document["diagnosis"] = diagnosis(bundle_dir, document)
    return document
