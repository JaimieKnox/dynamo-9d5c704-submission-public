"""Register lagged critic streams with seam-invalidated lag pads."""

def registered_stream(values, lag, init_value, segments=None):
    T = len(values)
    out = [0.0] * T
    for t in range(T):
        src = t - lag
        if src < 0:
            out[t] = float(init_value)
        elif segments is not None and segments[src] != segments[t]:
            out[t] = float(init_value)
        else:
            out[t] = float(values[src])
    return out
