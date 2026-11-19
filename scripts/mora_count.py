"""Count mora and estimate line durations for a JSON array on stdin.

Usage:
  py mora_count.py < lines.json

Each item: {"speaker": "...", "text": "kanji line", "kana": "kana reading",
            "type": "statement|question|exclamation"}
"""
import json
import sys

SPEED = {"calm": 7.0, "emotional": 6.0, "urgent": 8.5}
SMALL = set("ゃゅょぁぃぅぇぉゎ")


def to_hiragana(s):
    out = []
    for ch in s:
        o = ord(ch)
        out.append(chr(o - 0x60) if 0x30A1 <= o <= 0x30F6 else ch)
    return "".join(out)


def count_mora(kana):
    n = 0
    for ch in to_hiragana(kana):
        if ch in SMALL:
            continue
        if ch in ("ー", "っ", "ん"):
            n += 1
        elif "ぁ" <= ch <= "ゖ":
            n += 1
    return n


def density(t):
    if "！" in t or "!" in t:
        return 0.9
    if "？" in t or "?" in t:
        return 1.1
    if "…" in t or "..." in t:
        return 0.8
    return 1.0


def main():
    data = json.load(sys.stdin)
    total, total_mora = 0.0, 0
    for row in data:
        m = count_mora(row["kana"])
        speed = SPEED["emotional"] if ("！" in row["text"] or "!" in row["text"]) else SPEED["calm"]
        dur = m / speed * density(row["text"]) + 0.4
        total_mora += m
        total += dur
        print("%-10s %-30s mora=%2d  %.2fs" % (row["speaker"], row["text"][:28], m, dur))
    print("-" * 60)
    print("total_mora=%d  dialogue=%.2fs" % (total_mora, total))


if __name__ == "__main__":
    main()
