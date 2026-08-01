"""Small public boundary around the verifier's private replay implementation.

Both entry points remain available for callers that use the older ``expected`` name.
"""

from refpkg import learner


def audit(bundle_dir):
    """Reconstruct a bundle using only the verifier-side model."""
    return learner.run_bundle(bundle_dir)


def expected(bundle_dir):
    """Compatibility spelling for consumers of the reference package."""
    return audit(bundle_dir)
