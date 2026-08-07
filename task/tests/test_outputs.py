"""Black-box acceptance checks for the ledgers left in the output mount.

Expectations are sealed by ``derive_expectations`` before this module loads. The candidate
package therefore contributes observations only, never the values used as the oracle.
"""

import json
import os
from pathlib import Path

import pytest

BASE = os.path.dirname(os.path.abspath(__file__))
SEAL_PATH = os.path.join(BASE, "sealed_expectations.json")
SEALED_INPUTS = os.path.join(BASE, "inputs")
OUTPUT_MOUNT = "/app/out"
RUN_MOUNT = "/app/runs"
ROUNDING_ERROR = 1e-6
_OUTPUT_ROOT = Path(OUTPUT_MOUNT).resolve()

ROW_INTEGERS = ("step", "target_epoch", "dropped_nonresident")
ROW_DECIMALS = (
    "mean_vtrace_target",
    "mean_pg_advantage",
    "mean_is_weight",
    "priority_sum_after",
)
FINAL_COUNTS = (
    "transitions_enqueued",
    "segments_registered",
    "segments_evicted",
    "draws",
    "draws_accepted",
    "unique_segments_drawn",
)


def _recording_directories(parent):
    names = []
    for candidate in os.listdir(parent):
        marker = os.path.join(parent, candidate, "manifest.json")
        if os.path.isfile(marker):
            names.append(candidate)
    return sorted(names)


def _decode(filename):
    with open(filename) as source:
        return json.load(source)


def _looks_integral(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return float(value).is_integer()


assert os.path.isfile(SEAL_PATH), "sealed expectations missing; run derive_expectations first"
with open(SEAL_PATH) as handle:
    SEALED = json.load(handle)
os.remove(SEAL_PATH)

_outputs = {}


def _require_ordinary_output(name):
    """Reject symlinks and path escapes before any graded read (R190)."""
    target = Path(OUTPUT_MOUNT) / ("%s.json" % name)
    assert target.exists(), "expected output file is absent: %s" % target
    assert not target.is_symlink(), "graded output must not be a symlink: %s" % target
    assert target.is_file(), "graded output must be an ordinary file: %s" % target
    cursor = target
    while True:
        assert not cursor.is_symlink(), "graded output path traverses a symlink: %s" % cursor
        if cursor == cursor.parent:
            break
        if cursor == _OUTPUT_ROOT:
            break
        cursor = cursor.parent
    resolved = target.resolve()
    assert _OUTPUT_ROOT == resolved or _OUTPUT_ROOT in resolved.parents, (
        "graded output escaped the output mount: %s" % resolved
    )
    return str(target)


def _emitted(name):
    if name not in _outputs:
        target = _require_ordinary_output(name)
        _outputs[name] = _decode(target)
    return _outputs[name]


class ReplayCase:
    """Lazy access to one candidate ledger and its sealed peer."""

    def __init__(self, name):
        self.name = name
        self.input_dir = os.path.join(SEALED_INPUTS, name)

    @property
    def output(self):
        return _emitted(self.name)

    @property
    def model(self):
        assert self.name in SEALED, "sealed expectations missing bundle %s" % self.name
        return SEALED[self.name]

    @property
    def declared_steps(self):
        return _decode(os.path.join(self.input_dir, "manifest.json"))["learner_steps"]

    def row_pairs(self):
        return zip(self.output["steps"], self.model["steps"])


CASES = [
    ReplayCase(name)
    for name in _recording_directories(SEALED_INPUTS)
]


def test_measurements_reproduce_replayed_values():
    """Check every floating row field against a sealed replay, not a stored answer file in /app."""
    for case in CASES:
        for produced, baseline in case.row_pairs():
            for key in ROW_DECIMALS:
                assert produced[key] == pytest.approx(
                    baseline[key], abs=ROUNDING_ERROR
                ), (
                    "%s step %d has %s=%r; replay gives %r"
                    % (
                        case.name,
                        baseline["step"],
                        key,
                        produced[key],
                        baseline[key],
                    )
                )


def test_each_mounted_run_has_a_well_formed_envelope():
    """Require a named JSON result with the three schema containers for every run."""
    mounted_names = _recording_directories(RUN_MOUNT)
    fixture_names = [case.name for case in CASES]
    missing_inputs = sorted(set(fixture_names).difference(mounted_names))
    assert missing_inputs == [], "graded recordings not mounted: %s" % missing_inputs

    for name in mounted_names:
        result = _emitted(name)
        assert isinstance(result, dict), "%s result is not an object" % name
        assert set(("bundle", "steps", "totals")).issubset(result), (
            "%s result is missing a required root member" % name
        )
        assert result["bundle"] == name, "%s result is labelled %r" % (
            name,
            result["bundle"],
        )
        assert isinstance(result["steps"], list), "%s steps is not a list" % name
        assert isinstance(result["totals"], dict), "%s totals is not an object" % name


def test_final_accounting_reproduces_replay():
    """Compare all exact run counters plus the rounded terminal priority mass."""
    for case in CASES:
        produced = case.output["totals"]
        baseline = case.model["totals"]
        for key in FINAL_COUNTS:
            assert key in produced, "%s totals is missing %s" % (case.name, key)
            assert int(produced[key]) == baseline[key], (
                "%s totals.%s=%r; replay gives %d"
                % (case.name, key, produced[key], baseline[key])
            )

        assert "priority_sum_final" in produced, (
            "%s totals is missing priority_sum_final" % case.name
        )
        assert produced["priority_sum_final"] == pytest.approx(
            baseline["priority_sum_final"], abs=ROUNDING_ERROR
        ), (
            "%s terminal priority sum is %r; replay gives %r"
            % (
                case.name,
                produced["priority_sum_final"],
                baseline["priority_sum_final"],
            )
        )


def test_row_table_is_complete_ordered_and_typed():
    """Validate manifest length, ordinal continuity, and each schema value category."""
    for case in CASES:
        table = case.output["steps"]
        assert len(table) == case.declared_steps, (
            "%s has %d rows but declares %d steps"
            % (case.name, len(table), case.declared_steps)
        )
        for ordinal, row in enumerate(table):
            assert isinstance(row, dict), "%s row %d is not an object" % (
                case.name,
                ordinal,
            )
            assert row.get("step") == ordinal, "%s row %d reports ordinal %r" % (
                case.name,
                ordinal,
                row.get("step"),
            )
            for key in ROW_INTEGERS:
                assert _looks_integral(row.get(key)), (
                    "%s row %d has non-integral %s=%r"
                    % (case.name, ordinal, key, row.get(key))
                )

            accepted = row.get("sampled")
            assert isinstance(accepted, list), "%s row %d sampled is not a list" % (
                case.name,
                ordinal,
            )
            assert all(_looks_integral(slot) for slot in accepted), (
                "%s row %d sampled contains a non-integral slot: %r"
                % (case.name, ordinal, accepted)
            )
            for key in ROW_DECIMALS:
                value = row.get(key)
                assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                    "%s row %d has non-numeric %s=%r"
                    % (case.name, ordinal, key, value)
                )


def test_target_epoch_timeline_reproduces_replay():
    """Compare the selected target generation at every ordinal."""
    for case in CASES:
        for produced, baseline in case.row_pairs():
            assert int(produced["target_epoch"]) == baseline["target_epoch"], (
                "%s step %d selects target %r; replay selects %d"
                % (
                    case.name,
                    baseline["step"],
                    produced["target_epoch"],
                    baseline["target_epoch"],
                )
            )


def test_accepted_slot_stream_reproduces_replay():
    """Preserve accepted slot identity, order, and multiplicity for each batch."""
    for case in CASES:
        for produced, baseline in case.row_pairs():
            actual_stream = [int(slot) for slot in produced["sampled"]]
            assert actual_stream == baseline["sampled"], (
                "%s step %d sampled %r; replay sampled %r"
                % (
                    case.name,
                    baseline["step"],
                    actual_stream,
                    baseline["sampled"],
                )
            )


def test_rejected_draw_timeline_reproduces_replay():
    """Compare the count of nonresident selections discarded at every step."""
    for case in CASES:
        for produced, baseline in case.row_pairs():
            actual_count = int(produced["dropped_nonresident"])
            assert actual_count == baseline["dropped_nonresident"], (
                "%s step %d drops %d selections; replay drops %d"
                % (
                    case.name,
                    baseline["step"],
                    actual_count,
                    baseline["dropped_nonresident"],
                )
            )
