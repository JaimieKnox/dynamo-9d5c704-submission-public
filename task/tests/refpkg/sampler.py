"""Deterministic priority proportional sampler.

The stream is reseeded from the bundle sampler seed and the learner step index, so a
learner step draws the same sequence of unit variates no matter where the replay starts.
"""

_MASK = (1 << 64) - 1
_GOLDEN = 0x9E3779B97F4A7C15


class SplitMix64:
    def __init__(self, seed):
        self.state = seed & _MASK

    def next_u64(self):
        self.state = (self.state + _GOLDEN) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def next_unit(self):
        return (self.next_u64() >> 11) * (2.0 ** -53)


def step_stream(sampler_seed, step):
    return SplitMix64((sampler_seed ^ ((step * _GOLDEN) & _MASK)) & _MASK)


def draw(sampler_seed, step, count, priorities, total):
    """Return `count` registry positions drawn in proportion to `priorities`."""
    rng = step_stream(sampler_seed, step)
    picks = []
    for _ in range(count):
        target = rng.next_unit() * total
        acc = 0.0
        chosen = len(priorities) - 1
        for position, priority in enumerate(priorities):
            acc += priority
            if target < acc:
                chosen = position
                break
        picks.append(chosen)
    return picks
