"""Truncated importance weighted value targets and policy gradient advantages.

The backward recursion carries the corrected target while the per step temporal
difference is formed against the raw snapshot values, not against the corrected ones.
Both series share the same bootstrap slot at position `length`.
"""


def vtrace(rewards, values, bootstrap, rhos, cs, gamma):
    length = len(rewards)
    raw = list(values) + [bootstrap]
    targets = [0.0] * (length + 1)
    targets[length] = bootstrap
    for k in range(length - 1, -1, -1):
        delta = rhos[k] * (rewards[k] + gamma * raw[k + 1] - values[k])
        targets[k] = values[k] + delta + gamma * cs[k] * (targets[k + 1] - raw[k + 1])
    advantages = []
    for k in range(length):
        advantages.append(rhos[k] * (rewards[k] + gamma * targets[k + 1] - values[k]))
    return targets[:length], advantages
