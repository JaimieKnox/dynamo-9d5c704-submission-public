"""Verifier for the replay auditor task.

One test function per numbered success criterion of instruction.md. Expectations are
recomputed at verify time by tests/reference.py from tests/inputs, the verifier's own copy
of the recorded bundle inputs, so they cannot be shifted by editing anything under /app.
"""

import json
import os

import pytest

import reference

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
INPUTS_DIR = os.path.join(TESTS_DIR, "inputs")
OUT_DIR = "/app/out"
RUNS_DIR = "/app/runs"
TOL = 1e-6

STEP_INT_FIELDS = ("step", "target_epoch", "dropped_nonresident")
STEP_FLOAT_FIELDS = (
    "mean_vtrace_target",
    "mean_pg_advantage",
    "mean_is_weight",
    "priority_sum_after",
)
TOTAL_INT_FIELDS = (
    "transitions_enqueued",
    "segments_registered",
    "segments_evicted",
    "draws",
    "draws_accepted",
    "unique_segments_drawn",
)

BUNDLES = sorted(
    name
    for name in os.listdir(INPUTS_DIR)
    if os.path.isfile(os.path.join(INPUTS_DIR, name, "manifest.json"))
)


def _is_int(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, float) and float(value).is_integer()


def _load_document(bundle):
    path = os.path.join(OUT_DIR, bundle + ".json")
    assert os.path.isfile(path), "missing audit document %s" % path
    with open(path) as handle:
        return json.load(handle)


DOCUMENTS = {}
EXPECTED = {}


def _document(bundle):
    if bundle not in DOCUMENTS:
        DOCUMENTS[bundle] = _load_document(bundle)
    return DOCUMENTS[bundle]


def _expectation(bundle):
    if bundle not in EXPECTED:
        EXPECTED[bundle] = reference.expected(os.path.join(INPUTS_DIR, bundle))
    return EXPECTED[bundle]


def test_audit_document_per_bundle():
    """Criterion 1: every bundle under /app/runs has a parseable audit document with the
    four top level keys of the output schema."""
    listed = sorted(
        name
        for name in os.listdir(RUNS_DIR)
        if os.path.isfile(os.path.join(RUNS_DIR, name, "manifest.json"))
    )
    assert set(BUNDLES).issubset(set(listed)), (
        "run bundles missing from %s: %s" % (RUNS_DIR, sorted(set(BUNDLES) - set(listed)))
    )
    for bundle in listed:
        document = _document(bundle)
        assert isinstance(document, dict), "%s: audit document is not a JSON object" % bundle
        for key in ("bundle", "steps", "totals", "diagnosis"):
            assert key in document, "%s: audit document has no %r key" % (bundle, key)
        assert document["bundle"] == bundle, (
            "%s: bundle field is %r" % (bundle, document["bundle"])
        )
        assert isinstance(document["steps"], list), "%s: steps is not an array" % bundle
        assert isinstance(document["totals"], dict), "%s: totals is not an object" % bundle
        assert isinstance(document["diagnosis"], dict), (
            "%s: diagnosis is not an object" % bundle
        )


def test_step_ledger_shape():
    """Criterion 2: steps covers every learner step of the bundle in ascending order with
    every schema field present and of the declared type."""
    for bundle in BUNDLES:
        manifest_path = os.path.join(INPUTS_DIR, bundle, "manifest.json")
        with open(manifest_path) as handle:
            learner_steps = json.load(handle)["learner_steps"]
        steps = _document(bundle)["steps"]
        assert len(steps) == learner_steps, (
            "%s: %d step entries, expected %d" % (bundle, len(steps), learner_steps)
        )
        for index, record in enumerate(steps):
            assert isinstance(record, dict), "%s step %d: not an object" % (bundle, index)
            assert record.get("step") == index, (
                "%s: step entry %d reports step %r" % (bundle, index, record.get("step"))
            )
            for field in STEP_INT_FIELDS:
                assert _is_int(record.get(field)), (
                    "%s step %d: %s is %r, expected an integer"
                    % (bundle, index, field, record.get(field))
                )
            drawn = record.get("sampled")
            assert isinstance(drawn, list), (
                "%s step %d: sampled is %r, expected an array" % (bundle, index, drawn)
            )
            for slot in drawn:
                assert _is_int(slot), (
                    "%s step %d: sampled holds %r, expected integers" % (bundle, index, slot)
                )
            for field in STEP_FLOAT_FIELDS:
                value = record.get(field)
                assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                    "%s step %d: %s is %r, expected a number"
                    % (bundle, index, field, value)
                )


def test_target_epoch_per_step():
    """Criterion 3: target_epoch on every step is the target epoch the contract puts in
    force for that step."""
    for bundle in BUNDLES:
        got = _document(bundle)["steps"]
        expected = _expectation(bundle)["steps"]
        for record, want in zip(got, expected):
            assert int(record["target_epoch"]) == want["target_epoch"], (
                "%s step %d: target_epoch is %r, expected %d"
                % (bundle, want["step"], record["target_epoch"], want["target_epoch"])
            )


def test_accepted_draw_slot_sequences():
    """Criterion 4: sampled on every step is the exact ordered slot sequence of that
    step's accepted draws, repeats included."""
    for bundle in BUNDLES:
        got = _document(bundle)["steps"]
        expected = _expectation(bundle)["steps"]
        for record, want in zip(got, expected):
            drawn = [int(slot) for slot in record["sampled"]]
            assert drawn == want["sampled"], (
                "%s step %d: sampled is %r, expected %r"
                % (bundle, want["step"], drawn, want["sampled"])
            )


def test_rejected_draw_counts():
    """Criterion 5: dropped_nonresident on every step is the exact number of draws that
    step rejected."""
    for bundle in BUNDLES:
        got = _document(bundle)["steps"]
        expected = _expectation(bundle)["steps"]
        for record, want in zip(got, expected):
            assert int(record["dropped_nonresident"]) == want["dropped_nonresident"], (
                "%s step %d: dropped_nonresident is %r, expected %d"
                % (
                    bundle,
                    want["step"],
                    record["dropped_nonresident"],
                    want["dropped_nonresident"],
                )
            )


def test_step_aggregates():
    """Criterion 6: the four per step aggregates match the contract to six decimal
    places."""
    for bundle in BUNDLES:
        got = _document(bundle)["steps"]
        expected = _expectation(bundle)["steps"]
        for record, want in zip(got, expected):
            for field in STEP_FLOAT_FIELDS:
                assert record[field] == pytest.approx(want[field], abs=TOL), (
                    "%s step %d: %s is %r, expected %r"
                    % (bundle, want["step"], field, record[field], want[field])
                )


def test_run_totals():
    """Criterion 7: totals holds the seven run totals, the six counts exactly and
    priority_sum_final to six decimal places."""
    for bundle in BUNDLES:
        got = _document(bundle)["totals"]
        want = _expectation(bundle)["totals"]
        for field in TOTAL_INT_FIELDS:
            assert field in got, "%s: totals has no %r key" % (bundle, field)
            assert int(got[field]) == want[field], (
                "%s: totals.%s is %r, expected %d" % (bundle, field, got[field], want[field])
            )
        assert "priority_sum_final" in got, "%s: totals has no priority_sum_final" % bundle
        assert got["priority_sum_final"] == pytest.approx(
            want["priority_sum_final"], abs=TOL
        ), (
            "%s: totals.priority_sum_final is %r, expected %r"
            % (bundle, got["priority_sum_final"], want["priority_sum_final"])
        )


def test_first_divergent_step():
    """Criterion 8: diagnosis.first_divergent_step is the first learner step whose
    recorded digest differs from the contract's, or -1 when none differs."""
    for bundle in BUNDLES:
        got = _document(bundle)["diagnosis"]
        want = _expectation(bundle)["diagnosis"]
        assert "first_divergent_step" in got, (
            "%s: diagnosis has no first_divergent_step key" % bundle
        )
        value = got["first_divergent_step"]
        assert _is_int(value), (
            "%s: first_divergent_step is %r, expected an integer" % (bundle, value)
        )
        assert int(value) == want["first_divergent_step"], (
            "%s: first_divergent_step is %r, expected %d"
            % (bundle, value, want["first_divergent_step"])
        )


def test_recorded_defect_mode():
    """Criterion 9: diagnosis.defect is the mode /app/docs/defect-modes.md selects for the
    bundle."""
    for bundle in BUNDLES:
        got = _document(bundle)["diagnosis"]
        want = _expectation(bundle)["diagnosis"]
        assert "defect" in got, "%s: diagnosis has no defect key" % bundle
        assert want["defect"] in reference.MODES, (
            "%s: reference selected %r, which is not a documented mode"
            % (bundle, want["defect"])
        )
        assert got["defect"] == want["defect"], (
            "%s: defect is %r, expected %r" % (bundle, got["defect"], want["defect"])
        )
