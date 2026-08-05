"""Segment formation inside episode boundaries."""


class Segment:
    def __init__(self, episode_id, t0, rows, cut, boot_obs_id):
        self.episode_id = episode_id
        self.t0 = t0
        self.rows = rows
        self.length = len(rows)
        self.cut = cut
        self.boot_obs_id = boot_obs_id
        self.start_index = None
        self.complete_index = None
        self.frozen_epoch = None
        self.ready_step = None

    @property
    def residency_index(self):
        """Admission index that decides whether the segment is still drawable."""
        return self.start_index


def group_episodes(rows):
    episodes = {}
    for row in rows:
        episodes.setdefault(row["episode_id"], []).append(row)
    for key in episodes:
        episodes[key].sort(key=lambda row: row["t"])
    return episodes


def build_segments(episodes, n_step):
    """Every segment the contract can form, keyed by its episode and start offset."""
    out = []
    for episode_id in sorted(episodes):
        rows = episodes[episode_id]
        count = len(rows)
        for t0 in range(count):
            cut = None
            last = None
            for j in range(t0, min(count, t0 + n_step)):
                if rows[j]["terminated"]:
                    cut, last = "terminated", j
                    break
                if rows[j]["truncated"]:
                    cut, last = "truncated", j
                    break
                if j - t0 + 1 == n_step:
                    cut, last = "window", j
                    break
            if cut is None:
                continue
            if cut == "terminated":
                boot = None
            elif cut == "truncated":
                boot = rows[last]["obs_id"]
            else:
                if last + 1 >= count:
                    continue
                boot = rows[last + 1]["obs_id"]
            out.append(Segment(episode_id, t0, rows[t0:last + 1], cut, boot))
    return out
