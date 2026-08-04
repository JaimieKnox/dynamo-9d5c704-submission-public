# Priority proportional sampler (normative)

The sampler is fully specified here so that a replay is reproducible from the bundle alone.
An implementation of it is already present in the auditor and needs no changes.

## Stream

Each learner step uses its own stream. For bundle seed `S` and learner step `s`, all
arithmetic on 64 bit unsigned integers modulo `2 ** 64` with `G = 0x9E3779B97F4A7C15`:

    state = S xor (s * G)

    next_u64():
        state = state + G
        z = state
        z = (z xor (z >> 30)) * 0xBF58476D1CE4E5B9
        z = (z xor (z >> 27)) * 0x94D049BB133111EB
        return z xor (z >> 31)

    next_unit():
        return (next_u64() >> 11) * 2 ** -53

## Selection

Let `p[0], p[1], ..., p[N-1]` be the priorities of the ledger entries in ledger position
order and `P` their sum. One draw is

    target = next_unit() * P
    acc = 0.0
    for i in 0 .. N-1:
        acc = acc + p[i]
        if target < acc:
            return i
    return N - 1

The comparison is strict `target < acc`, and the running sum is accumulated in ledger
position order in float64. A step performs `batch_size` consecutive draws from its stream.
