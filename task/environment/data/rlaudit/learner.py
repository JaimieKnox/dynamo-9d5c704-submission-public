"""Learner replay orchestration."""

import json
import math
import os

from . import ingest
from . import params
from . import sampler
from . import segments as segmod
from .buffer import PriorityRegistry, TransitionBuffer
from .vtrace import vtrace


def _load_features(bundle_dir):
    with open(os.path.join(bundle_dir, "features.json")) as handle:
        return json.load(handle)


def _round6(value):
    return round(value, 6)


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


def run_bundle(bundle_dir):
    """Audit one run bundle."""
    with open(os.path.join(bundle_dir, "manifest.json")) as handle:
        manifest = json.load(handle)
    feats = _load_features(bundle_dir)
    epochs = params.load_epochs(bundle_dir)
    rows = ingest.load_shards(bundle_dir)
    admissions = ingest.load_admissions(bundle_dir)
    episodes = segmod.group_episodes(rows)
    all_segments = segmod.build_segments(episodes, manifest["n_step"])
    gamma = manifest["gamma"]
    rho_bar = manifest["rho_bar"]
    c_bar = manifest["c_bar"]
    alpha = manifest["alpha"]
    beta = manifest["beta"]
    priority_eps = manifest["priority_eps"]
    buffer = TransitionBuffer(manifest["buffer_capacity"])
    registry = PriorityRegistry()
    pending = rows
    unregistered = all_segments
    step_records = []
    total_draws = 0
    total_accepted = 0
    drawn = set()
    for step in range(manifest["learner_steps"]):
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
        attempted_weights = []
        updates = {}
        if size > 0 and total > 0.0:
            picks = sampler.draw(
                manifest["sampler_seed"], step, manifest["batch_size"], registry.priorities, total
            )
            total_draws += len(picks)
            for position in picks:
                segment = registry.segments[position]
                raw_weight = (size * (registry.priorities[position] / total)) ** (-beta)
                attempted_weights.append(raw_weight)
                if not buffer.is_resident(segment.residency_index):
                    dropped += 1
                    continue
                targets, advantages = segment_stats(
                    segment, feats, ep_params, gamma, rho_bar, c_bar
                )
                sampled.append(segment.rows[0]["_slot"])
                target_pool.extend(targets)
                advantage_pool.extend(advantages)
                weights.append(raw_weight)
                magnitude = 0.0
                for value in advantages:
                    magnitude += abs(value)
                updates[position] = (magnitude / len(advantages) + priority_eps) ** alpha
                total_accepted += 1
                drawn.add(position)

        if weights:
            top = max(attempted_weights)
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
        if not buffer.is_resident(segment.residency_index):
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

