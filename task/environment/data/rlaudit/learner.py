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
    """Audit one run bundle.

    The supporting modules under this package survived. The learner step loop that admits
    visible transitions, registers segments, draws a batch, scores accepted draws and
    writes priorities back did not, and has to be rebuilt against /app/docs.
    """
    raise NotImplementedError("learner replay orchestration is not implemented")

