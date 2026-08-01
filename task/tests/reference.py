"""Expose verifier-side reconstruction without leaking its implementation to the task."""

from refpkg import learner


def _reconstruct(recording_path):
    return learner.run_bundle(recording_path)


def expected(recording_path):
    """Return the ledger implied by an untouched recording fixture."""
    return _reconstruct(recording_path)


def audit(recording_path):
    """Retain the audit entry point used by external verifier callers."""
    return _reconstruct(recording_path)
