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
    visibility_lag = int(manifest.get("visibility_lag", 0))
    register_delay = int(manifest.get("register_delay", 0))
    sampler_priority_lag = int(manifest.get("sampler_priority_lag", 0))
    buffer = TransitionBuffer(manifest["buffer_capacity"])
    registry = PriorityRegistry()
    pending = rows
    unregistered = all_segments
    step_records = []
    total_draws = 0
    total_accepted = 0
    drawn = set()
    for step in range(manifest["learner_steps"]):
        watermark = ingest.visible_seq(admissions, step, visibility_lag)
        held_back = []
        for row in pending:
            if row["seq"] <= watermark:
                buffer.enqueue(row)
            else:
                held_back.append(row)
        pending = held_back

        live_epoch = params.epoch_for_step(
            step, manifest["target_refresh_interval"], len(epochs)
        )
        for segment in unregistered:
            if segment.ready_step is None and all("_index" in row for row in segment.rows):
                segment.mark_complete(step, epoch=live_epoch)

        due = []
        still_waiting = []
        for segment in unregistered:
            if segment.ready_step is None:
                still_waiting.append(segment)
                continue
            if step >= segment.ready_step + register_delay:
                due.append(segment)
            else:
                still_waiting.append(segment)
        due.sort(key=lambda seg: (seg.start_index, seg.complete_index))
        register_epoch = params.epoch_for_step(
            step, manifest["target_refresh_interval"], len(epochs)
        )
        for segment in due:
            registry.insert(segment, epoch=register_epoch, is_resident=buffer.is_resident)
        unregistered = still_waiting

        size, current_total, current_priorities = registry.pre_draw_state(buffer.is_resident)
        lagged = registry.lagged_sampler_vector()
        if sampler_priority_lag <= 0 or not lagged:
            draw_priorities = list(current_priorities)
        else:
            draw_priorities = list(lagged)
            if len(draw_priorities) < size:
                draw_priorities = draw_priorities + current_priorities[len(draw_priorities):]
            draw_priorities = draw_priorities[:size]
        draw_total = sum(draw_priorities)
        epoch = live_epoch
        sampled = []
        dropped = 0
        target_pool = []
        advantage_pool = []
        weights = []
        ordered_updates = []
        if size > 0 and draw_total > 0.0 and current_total > 0.0:
            picks = sampler.draw(
                manifest["sampler_seed"], step, manifest["batch_size"], draw_priorities, draw_total
            )
            total_draws += len(picks)
            for position in picks:
                segment = registry.segments[position]
                priority = draw_priorities[position]
                raw_weight = (size * (priority / current_total)) ** (-beta)
                if not buffer.is_resident(segment.residency_index):
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
                ordered_updates.append(
                    (position, (magnitude / len(advantages) + priority_eps) ** alpha)
                )
                total_accepted += 1
                drawn.add(position)

        if weights:
            top = max(weights)
            mean_weight = sum(w / top for w in weights) / len(weights)
        else:
            mean_weight = 0.0
        mean_target = sum(target_pool) / len(target_pool) if target_pool else 0.0
        mean_advantage = sum(advantage_pool) / len(advantage_pool) if advantage_pool else 0.0
        registry.snapshot_lag_before_commit()
        registry.commit_accepts(ordered_updates)
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
