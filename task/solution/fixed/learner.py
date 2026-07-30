"""Learner replay: per step admission, registration, sampling and priority write back,
plus the differential diagnosis of a recorded production ledger.
"""

import hashlib
import json
import math
import os

from . import ingest
from . import params
from . import sampler
from . import segments as segmod
from .buffer import PriorityRegistry, TransitionBuffer
from .vtrace import vtrace

# Candidate order of /app/docs/defect-modes.md. The reported defect is the first mode in
# this order whose replay reproduces every recorded digest.
MODES = (
    "none",
    "shard_local_order",
    "watermark_last_entry",
    "residency_by_last_transition",
    "truncated_bootstrap_acting_obs",
    "seed_constant_one",
    "weight_norm_over_all_draws",
)


def _load_features(bundle_dir):
    with open(os.path.join(bundle_dir, "features.json")) as handle:
        return json.load(handle)


def _round6(value):
    return round(value, 6)


def _micros(value):
    return int(round(value * 1000000))


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def step_digest(record):
    """Digest of one step ledger entry, per /app/docs/output-schema.md."""
    slots = ",".join(str(int(slot)) for slot in record["sampled"])
    canonical = "%d|%d|%s|%d|%d|%d|%d|%d" % (
        int(record["step"]),
        int(record["target_epoch"]),
        slots,
        int(record["dropped_nonresident"]),
        _micros(record["mean_vtrace_target"]),
        _micros(record["mean_pg_advantage"]),
        _micros(record["mean_is_weight"]),
        _micros(record["priority_sum_after"]),
    )
    return _digest(canonical)


def totals_digest(totals):
    """Digest of the run totals object, per /app/docs/output-schema.md."""
    canonical = "%d|%d|%d|%d|%d|%d|%d" % (
        int(totals["transitions_enqueued"]),
        int(totals["segments_registered"]),
        int(totals["segments_evicted"]),
        int(totals["draws"]),
        int(totals["draws_accepted"]),
        int(totals["unique_segments_drawn"]),
        _micros(totals["priority_sum_final"]),
    )
    return _digest(canonical)


def ledger_digests(document):
    return {
        "step_digests": [step_digest(record) for record in document["steps"]],
        "totals_digest": totals_digest(document["totals"]),
    }


def segment_stats(segment, feats, ep_params, gamma, rho_bar, c_bar):
    """Value targets and advantages for one segment under one target epoch snapshot."""
    rewards = []
    values = []
    rhos = []
    cs = []
    for row in segment.rows:
        feat = feats[row["obs_id"]]
        values.append(ep_params.value(feat))
        ratio = math.exp(ep_params.logp(feat, row["action"]) - row["behavior_logp"])
        rhos.append(min(rho_bar, ratio))
        cs.append(min(c_bar, ratio))
        rewards.append(row["reward"])
    if segment.cut == "terminated":
        boot = 0.0
    else:
        boot = ep_params.value(feats[segment.boot_obs_id])
    return vtrace(rewards, values, boot, rhos, cs, gamma)


def _watermark_last_entry(admissions, step):
    """Watermark of the last in force entry in file order rather than the greatest."""
    best = 0
    for entry in admissions:
        if entry["step"] <= step:
            best = entry["seq_watermark"]
    return best


def replay(bundle_dir, mode="none"):
    """Replay one recorded run under the contract, or under one documented deviation."""
    with open(os.path.join(bundle_dir, "manifest.json")) as handle:
        manifest = json.load(handle)
    feats = _load_features(bundle_dir)
    epochs = params.load_epochs(bundle_dir)
    rows = ingest.load_shards(bundle_dir)
    admissions = ingest.load_admissions(bundle_dir)

    if mode == "shard_local_order":
        admission_order = sorted(rows, key=lambda row: (row["actor_id"], row["seq"]))
    else:
        admission_order = rows

    episodes = segmod.group_episodes(rows)
    all_segments = segmod.build_segments(episodes, manifest["n_step"])
    if mode == "truncated_bootstrap_acting_obs":
        for segment in all_segments:
            if segment.cut == "truncated":
                segment.boot_obs_id = segment.rows[-1]["obs_id"]

    gamma = manifest["gamma"]
    rho_bar = manifest["rho_bar"]
    c_bar = manifest["c_bar"]
    alpha = manifest["alpha"]
    beta = manifest["beta"]
    priority_eps = manifest["priority_eps"]

    buffer = TransitionBuffer(manifest["buffer_capacity"])
    registry = PriorityRegistry()
    pending = admission_order
    unregistered = all_segments

    step_records = []
    total_draws = 0
    total_accepted = 0
    drawn = set()

    def anchor(segment):
        if mode == "residency_by_last_transition":
            return segment.complete_index
        return segment.start_index

    for step in range(manifest["learner_steps"]):
        if mode == "watermark_last_entry":
            watermark = _watermark_last_entry(admissions, step)
        else:
            watermark = ingest.visible_seq(admissions, step)
        held_back = []
        for row in pending:
            if row["seq"] <= watermark:
                buffer.enqueue(row)
            else:
                held_back.append(row)
        pending = held_back

        ready = []
        still_waiting = []
        for segment in unregistered:
            if all("_index" in row for row in segment.rows):
                segment.start_index = segment.rows[0]["_index"]
                segment.complete_index = max(row["_index"] for row in segment.rows)
                ready.append(segment)
            else:
                still_waiting.append(segment)
        ready.sort(key=lambda seg: (seg.complete_index, seg.start_index))
        for segment in ready:
            if mode == "seed_constant_one":
                registry.segments.append(segment)
                registry.priorities.append(1.0)
            else:
                registry.insert(segment)
        unregistered = still_waiting

        size = len(registry.segments)
        total = registry.total()
        epoch = params.epoch_for_step(step, manifest["target_refresh_interval"], len(epochs))
        ep_params = epochs[epoch]

        sampled = []
        dropped = 0
        target_pool = []
        advantage_pool = []
        weights = []
        norm_pool = []
        updates = {}

        if size > 0 and total > 0.0:
            picks = sampler.draw(
                manifest["sampler_seed"], step, manifest["batch_size"], registry.priorities, total
            )
            total_draws += len(picks)
            for position in picks:
                segment = registry.segments[position]
                raw_weight = (size * (registry.priorities[position] / total)) ** (-beta)
                if not buffer.is_resident(anchor(segment)):
                    dropped += 1
                    if mode == "weight_norm_over_all_draws":
                        norm_pool.append(raw_weight)
                    continue
                targets, advantages = segment_stats(
                    segment, feats, ep_params, gamma, rho_bar, c_bar
                )
                sampled.append(segment.rows[0]["_slot"])
                target_pool.extend(targets)
                advantage_pool.extend(advantages)
                weights.append(raw_weight)
                norm_pool.append(raw_weight)
                magnitude = 0.0
                for value in advantages:
                    magnitude += abs(value)
                updates[position] = (magnitude / len(advantages) + priority_eps) ** alpha
                total_accepted += 1
                drawn.add(position)

        if weights:
            top = max(norm_pool)
            mean_weight = sum(w / top for w in weights) / len(weights)
        else:
            mean_weight = 0.0
        mean_target = sum(target_pool) / len(target_pool) if target_pool else 0.0
        mean_advantage = sum(advantage_pool) / len(advantage_pool) if advantage_pool else 0.0

        for position, priority in updates.items():
            registry.priorities[position] = priority

        step_records.append(
            {
                "step": step,
                "target_epoch": epoch,
                "sampled": sampled,
                "dropped_nonresident": dropped,
                "mean_vtrace_target": _round6(mean_target),
                "mean_pg_advantage": _round6(mean_advantage),
                "mean_is_weight": _round6(mean_weight),
                "priority_sum_after": _round6(registry.total()),
            }
        )

    evicted = 0
    for segment in registry.segments:
        if not buffer.is_resident(anchor(segment)):
            evicted += 1

    return {
        "bundle": manifest["bundle"],
        "steps": step_records,
        "totals": {
            "transitions_enqueued": buffer.enqueued,
            "segments_registered": len(registry.segments),
            "segments_evicted": evicted,
            "draws": total_draws,
            "draws_accepted": total_accepted,
            "unique_segments_drawn": len(drawn),
            "priority_sum_final": _round6(registry.total()),
        },
    }


def _recorded_digests(bundle_dir):
    path = os.path.join(bundle_dir, "production", "ledger-digest.json")
    with open(path) as handle:
        return json.load(handle)


def diagnose(bundle_dir, faithful):
    """First divergent step and the defect mode that explains the recorded ledger."""
    recorded = _recorded_digests(bundle_dir)
    produced = ledger_digests(faithful)

    first_divergent = -1
    for index, digest in enumerate(produced["step_digests"]):
        if index >= len(recorded["step_digests"]) or digest != recorded["step_digests"][index]:
            first_divergent = index
            break

    defect = None
    for mode in MODES:
        if mode == "none":
            candidate = produced
        else:
            candidate = ledger_digests(replay(bundle_dir, mode))
        if (
            candidate["step_digests"] == recorded["step_digests"]
            and candidate["totals_digest"] == recorded["totals_digest"]
        ):
            defect = mode
            break

    return {"first_divergent_step": first_divergent, "defect": defect}


def run_bundle(bundle_dir):
    """Audit one run bundle.

    Returns the bundle's audit document as a dict in the schema of
    /app/docs/output-schema.md.
    """
    document = replay(bundle_dir, "none")
    document["diagnosis"] = diagnose(bundle_dir, document)
    return document
