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

    def insert(self, segment):
        """Append an entry seeded from the largest priority the ledger currently holds."""
        best = max(self.priorities) if self.priorities else 1.0
        self.segments.append(segment)
        self.priorities.append(best)
        return len(self.segments) - 1

    def total(self):
        return sum(self.priorities)
