"""The six anomaly-detection primitives that cover the whole insight catalog.
Pure functions, deterministic. Detectors compose these; the LLM never computes."""

def threshold(value, limit, direction="below"):
    if value is None or limit is None: return False
    return value < limit if direction == "below" else value > limit

def ratio_vs_baseline(value, baseline, ratio, direction="above"):
    if not baseline or value is None: return False          # null-guard: a None metric can't be a ratio
    r = value / baseline
    return r >= ratio if direction == "above" else r <= ratio

def pop_pct(current, prior):
    """period-over-period percent change"""
    if not prior or current is None: return 0.0             # null-guard: missing current ⇒ no change
    return (current - prior) / prior * 100.0

def zscore(value, mean, std):
    if not std or value is None or mean is None: return 0.0  # null-guard: missing inputs ⇒ neutral z
    return (value - mean) / std

def slope(series):
    """simple least-squares slope over an evenly-spaced series"""
    n = len(series)
    if n < 2: return 0.0
    xs = list(range(n)); mx = sum(xs)/n; my = sum(series)/n
    num = sum((x-mx)*(y-my) for x, y in zip(xs, series))
    den = sum((x-mx)**2 for x in xs) or 1
    return num/den

def crossing(prev, curr, level):
    """sign/level crossing between two consecutive observations"""
    if prev is None or curr is None: return None
    if prev >= level > curr: return "down"
    if prev <= level < curr: return "up"
    return None
