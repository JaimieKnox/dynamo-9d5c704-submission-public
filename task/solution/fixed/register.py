"""Register lagged critic streams."""

def registered_stream(values, lag, init_value):
    T = len(values)
    out = [0.0] * T
    for t in range(T):
        src = t - lag
        out[t] = float(values[src]) if src >= 0 else float(init_value)
    return out
