"""Grade agent GAE ledgers against sealed expectations."""
from __future__ import annotations
import json, os
from pathlib import Path
import pytest

OUTPUT_MOUNT = "/app/artifacts"
_OUTPUT_ROOT = Path(OUTPUT_MOUNT).resolve()
SEAL_PATH = "/tests/sealed_expectations.json"
ROUNDING_ERROR = 1e-6

with open(SEAL_PATH) as handle:
    SEALED = json.load(handle)
os.remove(SEAL_PATH)

_outputs = {}

def _require_ordinary_output(name):
    target = Path(OUTPUT_MOUNT) / ("%s.json" % name)
    assert target.exists(), "expected output file is absent: %s" % target
    assert not target.is_symlink(), "graded output must not be a symlink: %s" % target
    assert target.is_file(), "graded output must be an ordinary file: %s" % target
    cursor = target
    while True:
        assert not cursor.is_symlink(), "graded output path traverses a symlink: %s" % cursor
        if cursor == cursor.parent or cursor == _OUTPUT_ROOT:
            break
        cursor = cursor.parent
    resolved = target.resolve()
    assert _OUTPUT_ROOT == resolved or _OUTPUT_ROOT in resolved.parents, (
        "graded output escaped the output mount: %s" % resolved
    )
    return str(target)

def _emitted(name):
    if name not in _outputs:
        with open(_require_ordinary_output(name)) as fh:
            _outputs[name] = json.load(fh)
    return _outputs[name]

def _packs(parent):
    return sorted(n for n in os.listdir(parent) if os.path.isfile(os.path.join(parent, n, "meta.json")))

@pytest.mark.parametrize("name", _packs("/tests/inputs"))
def test_artifact_envelope(name):
    """Requirement 1: JSON envelope with pack, steps, and summary."""
    doc = _emitted(name)
    assert set(("pack", "steps", "summary")).issubset(doc)
    assert doc["pack"] == name
    assert isinstance(doc["steps"], list) and isinstance(doc["summary"], dict)

@pytest.mark.parametrize("name", _packs("/tests/inputs"))
def test_summary_matches_sealed(name):
    """Requirement 3: summary horizon/counts/means match sealed expectations."""
    produced = _emitted(name)["summary"]
    baseline = SEALED[name]["summary"]
    for key in ("horizon", "truncation_count", "termination_count"):
        assert produced[key] == baseline[key]
    for key in ("mean_advantage", "mean_return"):
        assert produced[key] == pytest.approx(baseline[key], abs=ROUNDING_ERROR)

@pytest.mark.parametrize("name", _packs("/tests/inputs"))
def test_per_index_values_match(name):
    """Requirement 2: one ascending steps row per index with sealed values."""
    produced_steps = _emitted(name)["steps"]
    baseline_steps = SEALED[name]["steps"]
    horizon = SEALED[name]["summary"]["horizon"]
    assert len(produced_steps) == horizon
    assert len(produced_steps) == len(baseline_steps)
    indices = [row["index"] for row in produced_steps]
    assert indices == list(range(horizon))
    for produced, baseline in zip(produced_steps, baseline_steps):
        assert produced["index"] == baseline["index"]
        assert produced["bootstrapped"] == baseline["bootstrapped"]
        assert produced["advantage"] == pytest.approx(baseline["advantage"], abs=ROUNDING_ERROR)
        assert produced["return"] == pytest.approx(baseline["return"], abs=ROUNDING_ERROR)