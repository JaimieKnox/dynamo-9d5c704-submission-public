"""Independent verifier reference for the learner contract."""

from refpkg import learner


def expected(bundle_dir):
    return learner.run_bundle(bundle_dir)


def audit(bundle_dir):
    return expected(bundle_dir)
