"""Time-weighted summary of EDEN_HDRUMBLE_TRACE files.

The trace logs a row only when a controller side's vibration value changes, so a value counts
for as long as it held, until the next row for the same side.
Usage: python analyze_trace_v2.py <name>=<file.csv> ...
"""
import csv
import sys


def load(path):
    rows = list(csv.DictReader(open(path, newline="")))
    sides = {}
    for r in rows:
        key = (r["npad_id"], r["device_index"])
        sides.setdefault(key, []).append(r)
    segments = []  # (duration_ms, peak_amp, low_freq, high_freq, low_amp, high_amp)
    for side_rows in sides.values():
        for cur, nxt in zip(side_rows, side_rows[1:]):
            dur = float(nxt["ms"]) - float(cur["ms"])
            la, ha = float(cur["low_amp"]), float(cur["high_amp"])
            segments.append((dur, max(la, ha), float(cur["low_freq"]), float(cur["high_freq"]), la, ha))
    span = float(rows[-1]["ms"]) - float(rows[0]["ms"])
    return rows, segments, span, len(sides)


def weighted_pct(pairs, p):
    pairs = sorted(pairs)
    total = sum(w for _, w in pairs)
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= p / 100 * total:
            return v
    return pairs[-1][0] if pairs else 0.0


def summarize(name, path):
    rows, segs, span, nsides = load(path)
    active = [s for s in segs if s[1] > 0.0]
    side_time = sum(s[0] for s in segs)
    active_time = sum(s[0] for s in active)
    amp = [(s[1], s[0]) for s in active]
    lf = [(s[2], s[0] * s[4]) for s in active if s[4] > 0]
    hf = [(s[3], s[0] * s[5]) for s in active if s[5] > 0]
    above = lambda t: sum(s[0] for s in active if s[1] >= t) / active_time * 100 if active_time else 0
    peak = max((s[1] for s in segs), default=0.0)
    return {
        "name": name,
        "seconds": span / 1000,
        "rows": len(rows),
        "vibrating_pct": active_time / side_time * 100 if side_time else 0,
        "p50": weighted_pct(amp, 50),
        "p90": weighted_pct(amp, 90),
        "p99": weighted_pct(amp, 99),
        "peak": peak,
        "above_0_1": above(0.1),
        "above_0_2": above(0.2),
        "lf50": weighted_pct(lf, 50),
        "hf50": weighted_pct(hf, 50),
        "lf_range": (min((s[2] for s in active), default=0), max((s[2] for s in active), default=0)),
        "hf_range": (min((s[3] for s in active), default=0), max((s[3] for s in active), default=0)),
    }


results = [summarize(*arg.split("=", 1)) for arg in sys.argv[1:]]
cols = [r["name"] for r in results]
lines = ["| | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
def row(label, fmt):
    lines.append("| " + label + " | " + " | ".join(fmt(r) for r in results) + " |")
row("Length of play", lambda r: f"{r['seconds']:.0f} s")
row("Rows (value changes)", lambda r: f"{r['rows']:,}")
row("Time vibrating (either band > 0)", lambda r: f"{r['vibrating_pct']:.0f} %")
row("Median amplitude while vibrating", lambda r: f"{r['p50']:.3f}")
row("90th percentile", lambda r: f"{r['p90']:.3f}")
row("99th percentile", lambda r: f"{r['p99']:.3f}")
row("Peak", lambda r: f"{r['peak']:.3f}")
row("Vibrating time at 0.1 or more", lambda r: f"{r['above_0_1']:.1f} %")
row("Vibrating time at 0.2 or more", lambda r: f"{r['above_0_2']:.1f} %")
row("Median low-band frequency (amplitude-weighted)", lambda r: f"{r['lf50']:.0f} Hz")
row("Median high-band frequency (amplitude-weighted)", lambda r: f"{r['hf50']:.0f} Hz")
row("Low-band range", lambda r: f"{r['lf_range'][0]:.0f}-{r['lf_range'][1]:.0f} Hz")
row("High-band range", lambda r: f"{r['hf_range'][0]:.0f}-{r['hf_range'][1]:.0f} Hz")
print("\n".join(lines))
