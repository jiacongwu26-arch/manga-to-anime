"""Plan shot durations and split them into render segments.

This tool reads a page plan from stdin and writes the timeline to stdout, so it
never opens a caller-supplied path.

Usage:
  py plan_duration.py --target 28 --unit 30 --segment 15,13 < page_plan.json > plan.json

Input (page_plan.json):
  {"p01": {"desc": "...", "parsed": {"panels": [
      {"content": "...", "bubbles": [
          {"type": "speech|thought|narration|shout|sfx|phone",
           "speaker": "charA",
           "text": "original line",
           "text_ja": "Japanese line",
           "text_ja_kana": "kana reading"}]}]}}}

--lang ja (default) requires text_ja_kana; a missing reading raises an error
instead of guessing mora. --lang zh uses `text` with a characters-per-second model.
"""
import argparse
import json
import math
import sys

SPEED_ZH = {"calm": 5.0, "emotional": 4.0, "urgent": 6.5}
SPEED_JA = {"calm": 7.0, "emotional": 6.0, "urgent": 8.5}
BASE = {"establishing": 3.5, "action": 2.5, "emotion": 2.2, "transition": 1.5, "mental": 3.0}
REACTION = 2.0
BREATH = 0.4
MIN_SHOT, MAX_SHOT = 1.2, 8.0

SMALL_KANA = set("ゃゅょぁぃぅぇぉゎ")

ESTABLISHING_WORDS = ("wide", "establish", "sky", "city", "landscape", "远景", "全景", "俯瞰")
ACTION_WORDS = ("run", "jump", "hit", "swing", "grab", "kick", "跑", "跳", "打", "挥", "抓")
MENTAL_WORDS = ("think", "remember", "gaze", "silent", "想", "回忆", "凝视", "沉默")
EMOTION_WORDS = ("close-up", "expression", "eyes", "特写", "表情", "眼神")


def to_hiragana(text):
    out = []
    for ch in str(text):
        o = ord(ch)
        if 0x30A1 <= o <= 0x30F6:
            out.append(chr(o - 0x60))
        else:
            out.append(ch)
    return "".join(out)


def count_mora(kana):
    n = 0
    for ch in to_hiragana(kana):
        if ch in SMALL_KANA:
            continue
        if ch in ("ー", "っ", "ん"):
            n += 1
        elif "ぁ" <= ch <= "ゖ":
            n += 1
    return n


def count_chars(text):
    return len("".join(ch for ch in str(text) if not ch.isspace()))


def density_factor(text):
    t = str(text or "")
    if "！" in t or "!" in t:
        return 0.9
    if "？" in t or "?" in t:
        return 1.1
    if "…" in t or "..." in t:
        return 0.8
    return 1.0


def line_duration_ja(kana, text):
    mora = count_mora(kana)
    if mora == 0:
        return 0.0
    t = str(text or "")
    speed = SPEED_JA["emotional"] if ("！" in t or "!" in t) else SPEED_JA["calm"]
    return mora / speed * density_factor(t) + BREATH


def line_duration_zh(text):
    chars = count_chars(text)
    if chars == 0:
        return 0.0
    speed = SPEED_ZH["emotional"] if ("！" in str(text)) else SPEED_ZH["calm"]
    return chars / speed * density_factor(text) + BREATH


def classify_panel(content):
    c = str(content or "").lower()
    if any(k in c for k in ESTABLISHING_WORDS):
        return "establishing"
    if any(k in c for k in ACTION_WORDS):
        return "action"
    if any(k in c for k in MENTAL_WORDS):
        return "mental"
    if any(k in c for k in EMOTION_WORDS):
        return "emotion"
    return "transition"


def bubble_line(b, lang):
    if lang == "ja":
        text = b.get("text_ja") or b.get("text") or ""
        kana = b.get("text_ja_kana")
        if not kana:
            raise ValueError("Japanese mode needs text_ja_kana: " + str(text))
        return text, line_duration_ja(kana, text)
    text = b.get("text") or ""
    return text, line_duration_zh(text)


def has_line(b, lang):
    t = (b.get("text_ja") or b.get("text")) if lang == "ja" else b.get("text")
    return isinstance(t, str) and bool(t.strip())


def build_shots(plan, page, lang):
    panels = plan.get(page, {}).get("parsed", {}).get("panels", [])
    shots = []
    for i, p in enumerate(panels):
        bubbles = p.get("bubbles", []) or []
        speech = [b for b in bubbles
                  if b.get("type") in ("speech", "shout", "phone") and has_line(b, lang)]
        other = [b for b in bubbles if b not in speech]
        ptype = classify_panel(p.get("content"))
        src = page + ".p" + str(i + 1)
        if speech:
            lines, d = [], 0.0
            for b in speech:
                text, dur = bubble_line(b, lang)
                lines.append(text)
                d += dur
            d += 0.8
            shots.append({"source": src, "type": "dialogue", "lines": lines,
                          "duration_s": round(min(MAX_SHOT, max(MIN_SHOT, d)), 2)})
            shots.append({"source": src, "type": "reaction", "lines": [],
                          "duration_s": REACTION})
        elif any(b.get("type") == "narration" for b in other):
            b = next(x for x in other if x.get("type") == "narration")
            text, dur = bubble_line(b, lang)
            shots.append({"source": src, "type": "narration",
                          "lines": [text] if text else [],
                          "duration_s": round(min(MAX_SHOT, max(BASE[ptype], dur)), 2)})
        else:
            shots.append({"source": src, "type": ptype, "lines": [],
                          "duration_s": BASE[ptype]})
    return shots


def reconcile(shots, target):
    total = sum(s["duration_s"] for s in shots)
    notes = []
    if target is None or abs(total - target) < 0.5:
        return shots, round(total, 2), notes
    if total > target:
        for kind, floor in (("transition", 1.2), ("reaction", 1.5), ("establishing", 2.5)):
            for s in shots:
                if s["type"] == kind and s["duration_s"] > floor and total > target:
                    cut = min(s["duration_s"] - floor, total - target)
                    s["duration_s"] = round(s["duration_s"] - cut, 2)
                    total = round(total - cut, 2)
                    notes.append("%s %s compressed %.2fs" % (s["source"], kind, cut))
        if total > target + 0.5:
            notes.append("content needs %.1fs > target %.1fs: compression exhausted; "
                         "split pages or drop named panels; never freeze the last frame"
                         % (total, target))
    elif total < target - 0.5:
        notes.append("content is %.1fs < target %.1fs: add shots; do not stretch "
                     "existing shots or pad with a still frame" % (total, target))
    return shots, round(total, 2), notes


def parse_segment_spec(spec):
    return [float(p.strip()) for p in str(spec).split(",") if p.strip()]


def pack_segments(shots, seg_lens):
    """Pack shots into segments of the given lengths without crossing boundaries."""
    notes = []
    segments, cur, cur_total, si = [], [], 0.0, 0
    for s in shots:
        limit = seg_lens[min(si, len(seg_lens) - 1)]
        if cur and cur_total + s["duration_s"] > limit + 1e-6:
            segments.append({"shots": cur, "duration_s": round(cur_total, 2), "limit_s": limit})
            si += 1
            cur, cur_total = [], 0.0
            limit = seg_lens[min(si, len(seg_lens) - 1)]
        if s["duration_s"] > limit + 1e-6:
            notes.append("%s is %.2fs, longer than segment limit %.2fs: split the shot"
                         % (s["source"], s["duration_s"], limit))
        cur.append(s)
        cur_total = round(cur_total + s["duration_s"], 2)
    if cur:
        segments.append({"shots": cur, "duration_s": round(cur_total, 2),
                         "limit_s": seg_lens[min(si, len(seg_lens) - 1)]})
    for i, seg in enumerate(segments, 1):
        seg["segment"] = i
        gap = round(seg["limit_s"] - seg["duration_s"], 2)
        if gap > 0.01:
            notes.append("segment %d is %.2fs of %.2fs: %.2fs short; add a shot "
                         "instead of stretching one" % (i, seg["duration_s"], seg["limit_s"], gap))
    return segments, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=float, default=None,
                    help="total render seconds, e.g. 28 for 15+13")
    ap.add_argument("--unit", type=float, default=30.0, help="planning unit seconds")
    ap.add_argument("--segment", default="15,13",
                    help="comma-separated segment seconds, used in order")
    ap.add_argument("--pages", default=None, help="comma-separated page keys")
    ap.add_argument("--lang", choices=["ja", "zh"], default="ja")
    args = ap.parse_args()

    plan = json.load(sys.stdin)
    pages = args.pages.split(",") if args.pages else sorted(plan)

    shots, notes = [], []
    for page in pages:
        if page not in plan:
            notes.append(page + " not in plan")
            continue
        try:
            shots.extend(build_shots(plan, page, args.lang))
        except ValueError as e:
            sys.stderr.write("ERROR: " + str(e) + "\n")
            sys.exit(2)

    shots, total, cut_notes = reconcile(shots, args.target)
    notes.extend(cut_notes)

    t = 0.0
    for i, s in enumerate(shots, 1):
        s["shot"] = i
        s["start_s"] = round(t, 2)
        t = round(t + s["duration_s"], 2)
        s["end_s"] = t
        f = max(5, int(math.ceil(s["duration_s"] * 24)))
        s["aligned_frames"] = f + (5 - f % 17) % 17

    segments, seg_notes = pack_segments(shots, parse_segment_spec(args.segment))
    notes.extend(seg_notes)
    t = 0.0
    for seg in segments:
        seg["start_s"] = round(t, 2)
        t = round(t + seg["duration_s"], 2)
        seg["end_s"] = t
        for s in seg["shots"]:
            s["segment"] = seg["segment"]

    result = {
        "total_seconds": round(t, 2),
        "target_seconds": args.target,
        "unit_seconds": args.unit,
        "segment_spec": parse_segment_spec(args.segment),
        "segments_count": len(segments),
        "lang": args.lang,
        "check": "ok" if (args.target is None or abs(t - args.target) <= 0.5) else "over_or_under",
        "notes": notes,
        "segments": segments,
        "shots": shots,
    }
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
