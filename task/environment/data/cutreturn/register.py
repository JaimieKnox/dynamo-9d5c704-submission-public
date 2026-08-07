"""Resolve registered critic values under meta lag."""

def registered_values(values, lag, init_value):
    return [float(v) for v in values]