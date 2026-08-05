"""Circular transition buffer and the learner's lazily cleaned priority registry."""


class TransitionBuffer:
    """Fixed capacity ring of transitions, one slot per admitted transition."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.slots = {}
        self.write_index = 0
        self.enqueued = 0

    def enqueue(self, row):
        index = self.write_index
        row["_index"] = index
        row["_slot"] = index % self.capacity
        self.slots[row["_slot"]] = row
        self.write_index += 1
        self.enqueued += 1
        return index

    def row_at_slot(self, slot):
        return self.slots.get(slot % self.capacity)

    def is_resident(self, index):
        """True while the transition admitted at `index` still owns its slot."""
        return self.write_index - index <= self.capacity


class PriorityRegistry:
    """Append only registry of segments. Entries are never removed, only re-weighted."""

    def __init__(self):
        self.segments = []
        self.priorities = []
        self._lagged = []

    def insert(self, segment, epoch=None, is_resident=None):
        """Append an entry seeded from the largest priority currently considered."""
        seed = 1.0
        if self.priorities:
            if is_resident is None:
                seed = max(self.priorities)
            else:
                resident_priorities = [
                    priority
                    for segment_i, priority in zip(self.segments, self.priorities)
                    if is_resident(segment_i.residency_index)
                ]
                if resident_priorities:
                    seed = max(resident_priorities)
                else:
                    seed = max(self.priorities)
        if segment._completion_epoch is not None:
            segment.stamp_epoch(segment._completion_epoch)
        elif epoch is not None:
            segment.stamp_epoch(epoch)
        self.segments.append(segment)
        self.priorities.append(seed)
        return len(self.segments) - 1

    def importance_mass(self, is_resident):
        """Mass used for draw gating and IS weights."""
        total = 0.0
        for segment, priority in zip(self.segments, self.priorities):
            if is_resident(segment.residency_index):
                total += priority
        return total

    def pre_draw_state(self, is_resident):
        """Shared pre-draw snapshot: N, P, and the current priority vector."""
        priorities = list(self.priorities)
        return len(self.segments), self.importance_mass(is_resident), priorities

    def commit_accepts(self, ordered_updates):
        """Apply accepted rewrite candidates in draw order."""
        for position, priority in ordered_updates:
            self.priorities[position] = priority

    def snapshot_lag_before_commit(self):
        """Freeze the sampler lag vector from the current priorities."""
        self._lagged = list(self.priorities)

    def lagged_sampler_vector(self):
        return list(self._lagged)

    def reweight(self, position, priority):
        self.priorities[position] = priority

    def total(self):
        return sum(self.priorities)
