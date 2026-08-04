"""Learner replay orchestration.

The replay engine walks each learner step once. Admission, segment registration and
the draw batch share the incremental state maintained across the loop rather than
recomputing it, so a long run stays linear in the number of transitions.
"""

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


def _slot_floor(buffer):
    """Oldest admission index the ring still owns."""
    return buffer.write_index - buffer.capacity


def _index_by_last_transition(all_segments):
    """Segments keyed by the stream position that completes them."""
    table = {}
    for segment in all_segments:
        table.setdefault(segment.rows[-1]["seq"], []).append(segment)
    return table


def _retarget_drawable(registry, floor, epoch):
    """Move ledger entries that are still drawable onto the newest target snapshot."""
    for segment in registry.segments:
        if segment.residency_index >= floor:
            segment.frozen_epoch = epoch


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
    completes = _index_by_last_transition(all_segments)
    gamma = manifest["gamma"]
    rho_bar = manifest["rho_bar"]
    c_bar = manifest["c_bar"]
    alpha = manifest["alpha"]
    beta = manifest["beta"]
    priority_eps = manifest["priority_eps"]
    interval = manifest["target_refresh_interval"]
    visibility = ingest.VisibilityCursor(
        admissions, int(manifest.get("visibility_lag", 0))
    )
    buffer = TransitionBuffer(manifest["buffer_capacity"])
    registry = PriorityRegistry()
    step_records = []
    stream = 0
    draw_mass = 0.0
    admitted_mass = 0.0
    total_draws = 0
    total_accepted = 0
    drawn = set()
    live_epoch = None
    for step in range(manifest["learner_steps"]):
        floor = _slot_floor(buffer)
        epoch = params.epoch_for_step(step, interval, len(epochs))
        watermark = visibility.advance(step)
        while stream < len(rows) and rows[stream]["seq"] <= watermark:
            row = rows[stream]
            buffer.enqueue(row)
            stream += 1
            for segment in completes.pop(row["seq"], ()):
                segment.start_index = segment.rows[0]["_index"]
                segment.complete_index = row["_index"]
                segment.frozen_epoch = epoch
                position = registry.insert(segment)
                admitted_mass += registry.priorities[position]

        if epoch != live_epoch:
            _retarget_drawable(registry, floor, epoch)
            live_epoch = epoch

        size = len(registry.segments)
        sampled = []
        dropped = 0
        target_pool = []
        advantage_pool = []
        weights = []
        updates = {}
        if size > 0 and draw_mass > 0.0:
            picks = sampler.draw(
                manifest["sampler_seed"],
                step,
                manifest["batch_size"],
                registry.priorities,
                draw_mass,
            )
            total_draws += len(picks)
            for position in picks:
                segment = registry.segments[position]
                raw_weight = (
                    size * (registry.priorities[position] / draw_mass)
                ) ** (-beta)
                if segment.residency_index < floor:
                    dropped += 1
                    continue
                ep_params = epochs[segment.frozen_epoch]
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
            mean_weight = sum(min(1.0, w) for w in weights) / len(weights)
        else:
            mean_weight = 0.0
        mean_target = sum(target_pool) / len(target_pool) if target_pool else 0.0
        mean_advantage = sum(advantage_pool) / len(advantage_pool) if advantage_pool else 0.0
        for position, priority in updates.items():
            admitted_mass += priority - registry.priorities[position]
            registry.reweight(position, priority)
        draw_mass = admitted_mass
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
