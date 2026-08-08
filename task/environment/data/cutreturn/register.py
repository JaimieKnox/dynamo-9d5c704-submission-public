"""Register lagged critic streams."""

def registered_stream(values, lag, init_value, segments=None):
    return [float(v) for v in values]
