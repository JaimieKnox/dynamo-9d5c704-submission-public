"""Advantage-mass and return-mass membership shared by the ledger."""
from .seam import open_used_cross_lag, segment_opens


def advantage_mass_indices(terminated, seam_edge, scale_pad, lag_b, segments):
    opens = segment_opens(segments)
    idxs = []
    for i, term in enumerate(terminated):
        if term:
            continue
        if seam_edge[i] and open_used_cross_lag(opens[segments[i]], lag_b, segments):
            continue
        if scale_pad[i]:
            continue
        idxs.append(i)
    return idxs


def return_mass_indices(terminated, scale_pad):
    return [i for i, term in enumerate(terminated) if (not term) and (not scale_pad[i])]


def fallback_mass_indices(terminated, horizon):
    live = [i for i in range(horizon) if not terminated[i]]
    return live if live else list(range(horizon))
