"""Resolve registered critic values under meta lag."""

def registered_values(values, lag, init_value):
    T = len(values)
    out = [0.0] * T
    for t in range(T):
        if t >= lag:
            out[t] = float(values[t - lag])
        else:
            out[t] = float(init_value)
    return out