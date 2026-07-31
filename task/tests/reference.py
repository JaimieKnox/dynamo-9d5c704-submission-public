"""Independent reference implementation of the learner contract.

Reads verifier-owned copies of the bundle inputs under tests/inputs and produces
the expected audit document for a bundle. Kept separate from the agent-visible
package so expectations cannot be shifted by editing /app.
"""

from refpkg import learner


def expected(bundle_dir):
    return learner.run_bundle(bundle_dir)


def audit(bundle_dir):
    return expected(bundle_dir)
