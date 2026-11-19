"""Measure motion stability of a rendered clip.

Usage:
  py check_motion.py --input clip.mp4

Prints metrics as JSON to stdout; redirect if you want a file. The input must be an
existing video file, and frames are extracted into a private temporary directory.

Notes:
  center_texture_delta is NOT face detection. It measures frame-to-frame
  high-frequency texture change in the central region. Dense textures (crowds,
  cityscapes, foliage) trigger it with no face present. Pull frames to confirm.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

import cv2
import numpy as np

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
SAFE_NAME = re.compile(r"^[\w .\-]+$")


def validate_media_path(raw):
    """Return an absolute path to an existing video file, or raise ValueError."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("empty path")
    if not SAFE_NAME.match(os.path.basename(raw)):
        raise ValueError("unsafe filename characters")
    p = os.path.realpath(raw)
    if not os.path.isfile(p):
        raise ValueError("not a regular file")
    if os.path.splitext(p)[1].lower() not in VIDEO_EXT:
        raise ValueError("unsupported extension")
    return p


def extract(video, tmp):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video,
                    os.path.join(tmp, "f_%05d.png")], check=True)
    return sorted(os.listdir(tmp))


def analyze(files, tmp):
    lums, flows, sharp, hi_deltas = [], [], [], []
    prev = prev_hi = None
    for name in files:
        img = cv2.imread(os.path.join(tmp, name))
        if img is None:
            continue
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lums.append(float(g.mean()))
        sharp.append(float(cv2.Laplacian(g, cv2.CV_64F).var()))

        h, w = g.shape
        crop = g[int(h * 0.15):int(h * 0.75), int(w * 0.25):int(w * 0.75)].astype(np.float32)
        hi = crop - cv2.GaussianBlur(crop, (0, 0), 2.0)
        if prev_hi is not None:
            hi_deltas.append(float(np.abs(hi - prev_hi).mean()))
        prev_hi = hi

        if prev is not None:
            f = cv2.calcOpticalFlowFarneback(prev, g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            flows.append(float(np.sqrt(f[..., 0] ** 2 + f[..., 1] ** 2).mean()))
        prev = g

    lums = np.array(lums)
    flows = np.array(flows) if flows else np.array([0.0])
    return {
        "frames": len(files),
        "flicker": round(float(np.abs(np.diff(lums)).mean()) if len(lums) > 1 else 0.0, 3),
        "warp_jerk": round(float(np.abs(np.diff(flows)).mean()) if len(flows) > 1 else 0.0, 3),
        "static_ratio": round(float((flows < 0.05).mean()), 3),
        "motion_mean": round(float(flows.mean()), 3),
        "motion_std": round(float(flows.std()), 3),
        "sharpness_mean": round(float(np.mean(sharp)), 1),
        "center_texture_delta": round(float(np.mean(hi_deltas)) if hi_deltas else 0.0, 2),
    }


def verdicts(m):
    issues = []
    if m["static_ratio"] > 0.5:
        issues.append("over half the frames barely move; may look like a still")
    if m["flicker"] > 6:
        issues.append("large frame-to-frame brightness jumps; possible flicker")
    if m["warp_jerk"] > 0.6:
        issues.append("motion discontinuity; possible dropped or duplicated frames")
    if m["sharpness_mean"] < 80:
        issues.append("low sharpness (Laplacian variance < 80)")
    if m["center_texture_delta"] > 2.5:
        issues.append("high center texture change: check for face boiling, but dense "
                      "backgrounds trigger this too; pull frames to confirm")
    if m["motion_std"] < 0.15 and m["static_ratio"] <= 0.5:
        issues.append("very uniform motion; may be a slow drift")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="path to an existing video file")
    args = ap.parse_args()

    try:
        video = validate_media_path(args.input)
    except ValueError as e:
        sys.stderr.write("ERROR: " + str(e) + "\n")
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        files = extract(video, tmp)
        m = analyze(files, tmp)
    m["verdict"] = verdicts(m)
    print(json.dumps(m, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
