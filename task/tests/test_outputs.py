"""Checks generated replay ledgers against verifier-owned source recordings.

The application tree is never used to derive answers.  A separate implementation consumes
the fixtures beside this file, and the emitted JSON is inspected independently by concern.
"""

import json
import os

import pytest

import reference

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE_ROOT = os.path.join(HERE, "inputs")
GENERATED_ROOT = "/app/out"
MOUNTED_RUNS = "/app/runs"
SIX_PLACES = 1e-6

WHOLE_STEP_VALUES = ("step", "target_epoch", "dropped_nonresident")
STEP_MEASUREMENTS = (
    "mean_vtrace_target",
    "mean_pg_advantage",
    "mean_is_weight",
    "priority_sum_after",
)
RUN_COUNTERS = (
    "transitions_enqueued",
    "segments_registered",
    "segments_evicted",
    "draws",
    "draws_accepted",
    "unique_segments_drawn",
)


def _bundle_names(root):
    return sorted(
        entry
        for entry in os.listdir(root)
        if os.path.isfile(os.path.join(root, entry, "manifest.json"))
    )


FIXTURE_BUNDLES = _bundle_names(FIXTURE_ROOT)
_actual_cache = {}
_reference_cache = {}


def _integer_like(item):
    return (
        not isinstance(item, bool)
        and isinstance(item, (int, float))
        and float(item).is_integer()
    )


def _read_json(path):
    with open(path) as stream:
        return json.load(stream)


def _actual(bundle):
    if bundle not in _actual_cache:
        filename = os.path.join(GENERATED_ROOT, bundle + ".json")
        assert os.path.isfile(filename), "%s was not generated" % filename
        _actual_cache[bundle] = _read_json(filename)
    return _actual_cache[bundle]


def _truth(bundle):
    if bundle not in _reference_cache:
        fixture = os.path.join(FIXTURE_ROOT, bundle)
        _reference_cache[bundle] = reference.audit(fixture)
    return _reference_cache[bundle]


def _paired_steps(bundle):
    return zip(_actual(bundle)["steps"], _truth(bundle)["steps"])


def test_terminal_run_accounting():
    """The accumulated counters and ending priority mass must describe the full replay."""
    for bundle in FIXTURE_BUNDLES:
        observed = _actual(bundle)["totals"]
        recomputed = _truth(bundle)["totals"]
        for counter in RUN_COUNTERS:
            assert counter in observed, "%s totals omitted %s" % (bundle, counter)
            assert int(observed[counter]) == recomputed[counter], (
                "%s totals.%s: got %r, wanted %d"
                % (bundle, counter, observed[counter], recomputed[counter])
            )
        assert "priority_sum_final" in observed, (
            "%s totals omitted priority_sum_final" % bundle
        )
        assert observed["priority_sum_final"] == pytest.approx(
            recomputed["priority_sum_final"], abs=SIX_PLACES
        ), (
            "%s ending priority mass: got %r, wanted %r"
            % (
                bundle,
                observed["priority_sum_final"],
                recomputed["priority_sum_final"],
            )
        )


def test_output_inventory_and_envelopes():
    """Every mounted recording needs a parseable, correctly labelled result envelope."""
    mounted = _bundle_names(MOUNTED_RUNS)
    absent = sorted(set(FIXTURE_BUNDLES) - set(mounted))
    assert not absent, "fixtures absent from %s: %s" % (MOUNTED_RUNS, absent)

    for bundle in mounted:
        payload = _actual(bundle)
        assert isinstance(payload, dict), "%s output must be an object" % bundle
        assert all(name in payload for name in ("bundle", "steps", "totals")), (
            "%s output lacks one or more required top-level fields" % bundle
        )
        assert payload["bundle"] == bundle, (
            "%s output identifies itself as %r" % (bundle, payload["bundle"])
        )
        assert isinstance(payload["steps"], list), "%s steps must be an array" % bundle
        assert isinstance(payload["totals"], dict), "%s totals must be an object" % bundle


def test_epoch_selected_for_each_learner_iteration():
    """The target generation reported at each iteration must equal recomputation."""
    for bundle in FIXTURE_BUNDLES:
        for observed, recomputed in _paired_steps(bundle):
            assert int(observed["target_epoch"]) == recomputed["target_epoch"], (
                "%s iteration %d uses epoch %r instead of %d"
                % (
                    bundle,
                    recomputed["step"],
                    observed["target_epoch"],
                    recomputed["target_epoch"],
                )
            )


def test_step_rows_follow_schema_and_manifest_length():
    """Step rows must be complete, ordered, and represented with the declared value kinds."""
    for bundle in FIXTURE_BUNDLES:
        manifest = _read_json(os.path.join(FIXTURE_ROOT, bundle, "manifest.json"))
        rows = _actual(bundle)["steps"]
        assert len(rows) == manifest["learner_steps"], (
            "%s emitted %d rows for %d learner steps"
            % (bundle, len(rows), manifest["learner_steps"])
        )

        for position, row in enumerate(rows):
            assert isinstance(row, dict), "%s row %d must be an object" % (
                bundle,
                position,
            )
            assert row.get("step") == position, (
                "%s row %d carries step %r" % (bundle, position, row.get("step"))
            )
            for field in WHOLE_STEP_VALUES:
                assert _integer_like(row.get(field)), (
                    "%s row %d field %s is not integer-valued: %r"
                    % (bundle, position, field, row.get(field))
                )

            slots = row.get("sampled")
            assert isinstance(slots, list), "%s row %d sampled must be an array" % (
                bundle,
                position,
            )
            assert all(_integer_like(slot) for slot in slots), (
                "%s row %d sampled contains a non-integer value: %r"
                % (bundle, position, slots)
            )
            for field in STEP_MEASUREMENTS:
                number = row.get(field)
                assert isinstance(number, (int, float)) and not isinstance(number, bool), (
                    "%s row %d field %s must be numeric, got %r"
                    % (bundle, position, field, number)
                )


def test_nonresident_draw_rejections():
    """The rejected-draw tally is checked separately for every learner iteration."""
    for bundle in FIXTURE_BUNDLES:
        for observed, recomputed in _paired_steps(bundle):
            assert int(observed["dropped_nonresident"]) == recomputed[
                "dropped_nonresident"
            ], (
                "%s iteration %d rejected %r draws; recomputation rejected %d"
                % (
                    bundle,
                    recomputed["step"],
                    observed["dropped_nonresident"],
                    recomputed["dropped_nonresident"],
                )
            )


def test_numeric_step_summaries():
    """All per-iteration measurements are compared at the required decimal tolerance."""
    for bundle in FIXTURE_BUNDLES:
        for observed, recomputed in _paired_steps(bundle):
            for field in STEP_MEASUREMENTS:
                assert observed[field] == pytest.approx(
                    recomputed[field], abs=SIX_PLACES
                ), (
                    "%s iteration %d field %s: got %r, wanted %r"
                    % (
                        bundle,
                        recomputed["step"],
                        field,
                        observed[field],
                        recomputed[field],
                    )
                )


def test_sampling_trace_retains_order_and_repetition():
    """Accepted slot identifiers must reproduce the reference draw stream verbatim."""
    for bundle in FIXTURE_BUNDLES:
        for observed, recomputed in _paired_steps(bundle):
            observed_slots = [int(slot) for slot in observed["sampled"]]
            assert observed_slots == recomputed["sampled"], (
                "%s iteration %d accepted %r; recomputation accepted %r"
                % (
                    bundle,
                    recomputed["step"],
                    observed_slots,
                    recomputed["sampled"],
                )
            )
