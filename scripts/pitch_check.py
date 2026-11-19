"""Compare median F0 across segments to check voice separation.

Usage:
  py pitch_check.py --input audio.wav
  py pitch_check.py --input audio.wav --segments "0-3,3-8,8-13"

Segments are start-end seconds. Without --segments the whole file is one segment.
"""
import argparse
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt


def f0_median(x, sr):
    sos = butter(4, [70, 400], btype="band", fs=sr, output="sos")
    y = sosfilt(sos, x)
    win, hop = int(0.04 * sr), int(0.02 * sr)
    vals = []
    for i in range(0, len(y) - win, hop):
        f = y[i:i + win]
        if np.sqrt(np.mean(f * f)) < 0.01:
            continue
        f = f - f.mean()
        ac = np.correlate(f, f, mode="full")[win - 1:]
        lo, hi = int(sr / 400), int(sr / 70)
        if hi >= len(ac):
            continue
        lag = lo + int(np.argmax(ac[lo:hi]))
        if ac[lag] > 0.3 * ac[0]:
            vals.append(sr / lag)
    return (float(np.median(vals)) if vals else 0.0), len(vals)


def parse_segments(spec, duration):
    if not spec:
        return [("all", 0.0, duration)]
    out = []
    for i, part in enumerate(spec.split(","), 1):
        a, b = part.split("-")
        out.append(("seg%d" % i, float(a), float(b)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--segments", default=None, help='e.g. "0-3,3-8,8-13"')
    args = ap.parse_args()

    x, sr = sf.read(args.input, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    dur = len(x) / sr
    print("sr=%d duration=%.2fs" % (sr, dur))

    medians = []
    for name, a, b in parse_segments(args.segments, dur):
        seg = x[int(a * sr):int(b * sr)]
        med, n = f0_median(seg, sr)
        medians.append(med)
        print("%-6s %5.1f-%5.1f  F0_median=%6.1f Hz  voiced_frames=%d" % (name, a, b, med, n))

    spoken = [m for m in medians if m > 0]
    if len(spoken) >= 2:
        spread = max(spoken) - min(spoken)
        print("spread=%.1f Hz" % spread)
        if spread < 25:
            print("WARNING: voices are close in pitch; use a clearer voice description")
    return 0


if __name__ == "__main__":
    sys.exit(main())
