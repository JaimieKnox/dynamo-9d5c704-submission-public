"""Target parameter snapshots: one value head and one policy head per refresh epoch."""

import json
import math
import os


class EpochParams:
    """Linear value head and linear policy head for a single target refresh epoch."""

    def __init__(self, value_w, value_b, policy_w, policy_b):
        self.value_w = value_w
        self.value_b = value_b
        self.policy_w = policy_w
        self.policy_b = policy_b

    def value(self, feat):
        acc = self.value_b
        for w, f in zip(self.value_w, feat):
            acc += w * f
        return acc

    def logp(self, feat, action):
        logits = []
        for row, bias in zip(self.policy_w, self.policy_b):
            acc = bias
            for w, f in zip(row, feat):
                acc += w * f
            logits.append(acc)
        top = max(logits)
        total = 0.0
        for z in logits:
            total += math.exp(z - top)
        return logits[action] - top - math.log(total)


def load_epochs(bundle_dir):
    """Load every epoch snapshot in ascending epoch order."""
    pdir = os.path.join(bundle_dir, "params")
    names = sorted(n for n in os.listdir(pdir) if n.startswith("epoch-") and n.endswith(".json"))
    epochs = []
    for name in names:
        with open(os.path.join(pdir, name)) as handle:
            raw = json.load(handle)
        epochs.append(
            EpochParams(raw["value_w"], raw["value_b"], raw["policy_w"], raw["policy_b"])
        )
    return epochs


def epoch_for_step(step, interval, n_epochs):
    """Target epoch in force for a learner step, clamped to the highest available snapshot."""
    epoch = step // interval
    if epoch > n_epochs - 1:
        epoch = n_epochs - 1
    return epoch
