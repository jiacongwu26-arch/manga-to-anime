# End-to-end walkthrough

Two pages, two characters: a child and an adult. Generic values; substitute your own.

The point of this walkthrough is not the output — it is **where the constraints fire**.

---

## Page 1: the review that catches four errors

### Raw machine parse (wrong in four places)

```json
{
  "p01": {"parsed": {"panels": [
    {"content": "A blonde girl holds a book and points down the stairs",
     "bubbles": [
       {"type": "speech", "speaker": "adult", "text": "Mom!"},
       {"type": "speech", "speaker": "child", "text": "What is it?"}
     ]},
    {"content": "A blonde woman sits at the table with her chin on her hand",
     "bubbles": [
       {"type": "speech", "speaker": "child", "text": "Oh my, then you must practice magic."}
     ]},
    {"content": "The woman pats the child's head",
     "bubbles": [
       {"type": "speech", "speaker": "adult", "text": "pat pat"}
     ]}
  ]}}
}
```

Four errors, all of them common:

| # | Error | Constraint |
|---|---|---|
| 1 | Hair described as blonde | C9 — grayscale pages cannot establish color |
| 2 | "Mom!" assigned to the adult | C4 — the child is the one calling out |
| 3 | "What is it?" assigned to the child | C4 — the adult answers |
| 4 | "pat pat" typed as speech | C5 — that is an sfx, not a line |

Nothing here is a rendering problem. The model will faithfully animate all four mistakes.

### After human review (Step 1.5)

```json
{
  "p01": {"parsed": {"panels": [
    {"content": "Child runs to the stairs and calls out; adult turns from the staircase",
     "bubbles": [
       {"type": "speech", "speaker": "child",
        "text_ja": "お母さん！", "text_ja_kana": "おかあさん！"},
       {"type": "speech", "speaker": "adult",
        "text_ja": "どうしたの？", "text_ja_kana": "どうしたの？"}
     ]},
    {"content": "Adult sits alone at the table, chin on hand, speaking gently",
     "bubbles": [
       {"type": "speech", "speaker": "adult",
        "text_ja": "あら、じゃあまずは練習を頑張らないとね。",
        "text_ja_kana": "あら、じゃあまずはれんしゅうをがんばらないとね。"}
     ]},
    {"content": "Adult closes her eyes and pats the child's head",
     "bubbles": [
       {"type": "sfx", "speaker": null,
        "text_ja": "そっと撫でる", "text_ja_kana": "そっとなでる"}
     ]}
  ]}}
```

Note panel 2: **only the adult is in frame**. The parser put the child's line there; the review moved it out. A panel that contains one character cannot carry the other character's dialogue.

Note panel 3: `sfx`, speaker `null`. No line, no voice.

---

## Page 2: where identity splits

### The mistake that ruins the episode

Page 2 has three panels:

1. The adult crouches and pats the child's head — "Of course you can."
2. Wide shot: sky, mountains, one small witch flying.
3. The adult's back, on a broom: "Almost there."

A naive parse sees "long-haired woman" in panel 1 and "long-haired person on a broom" in panel 3 and concludes they are the same character. They are not: panel 3 is the **child, grown up**. Panel 1's adult is the mother.

The error produces "the mother flies off to the destination alone" — the protagonist vanishes from her own story.

**How the review catches it**: compare clothing and accessories, not hair. A grown-up version of a character keeps a signature accessory (here, a brooch) but not the same outfit. When the outfits differ and the ages differ, treat them as two identities until proven otherwise.

### Second mistake on the same page

Panel 2 (wide, one small figure) and panel 3 (back view) are the same character at two scales. Do **not** turn them into two people. The wide shot is an establishing beat, not a new cast member.

---

## Timing: the ledger that says no

After review, the shots:

| Shot | Source | Type | Lines | mora | Duration |
|---|---|---|---|---:|---:|
| 1 | p01.p1 | dialogue | お母さん！ / どうしたの？ | 14 | 2.4s |
| 2 | p01.p1 | reaction | — | 0 | 2.0s |
| 3 | p01.p2 | dialogue | あら、じゃあまずは練習を頑張らないとね。 | 25 | 4.0s |
| 4 | p01.p2 | reaction | — | 0 | 2.0s |
| 5 | p01.p3 | sfx/action | — | 0 | 2.0s |
| 6 | p02.p1 | dialogue | もちろんよ。 | 5 | 1.1s |
| 7 | p02.p2 | establishing | — | 0 | 3.5s |
| 8 | p02.p3 | dialogue | もうすぐ着くわね。 | 8 | 1.5s |

Sum: 18.5s. Target for a 28s cut: **9.5s short**.

Two wrong fixes and one right fix:

- Wrong: stretch shot 8 from 1.5s to 11s. The character stands still for nine seconds. C13.
- Wrong: freeze the last frame for 9.5s. C13 again, worse.
- Right: add shots — an insert of the book, a beat on the adult's expression, a wider establishing shot of the destination as the wind picks up. Each new shot is a real cut with its own content.

The ledger script enforces this: it reports the gap and refuses to stretch.

```bash
python scripts/plan_duration.py --target 28 --unit 30 --segment 15,13 \
  < page_plan.json > plan.json
```

```
content is 18.5s < target 28.0s: add shots; do not stretch existing shots
segment 1 is 12.0s of 15.00s: 3.00s short; add a shot instead of stretching one
```

---

## Prompt: what the constraints turn into

```text
Convert this manga page into animation.

[References] 1 = official colored art of the child; 2 = official colored art of the adult;
             3 = manga page 1
[Character lock] follow the reference art for hair color, eye color, and costume.
                 Do not introduce any character not in the references.
[Dialogue] all lines in Japanese. The child has a bright young voice; the adult a calm
           mature voice. No BGM.
[Reading order] right to left, top to bottom.
  - Panel 1: the child calls out, the adult answers.
  - Panel 2: the adult alone at the table, chin on hand.
  - Panel 3: the adult pats the child's head. No dialogue; only the soft sound of cloth.
[Timeline] 0-3s panel 1; 3-6s panel 2; 6-9s panel 3; ...
[Order] the child asks, then the adult pats.
[Output] no text, subtitles, speech bubbles, or panel borders in frame.
```

Three things to notice:

1. **No color values.** It says "follow the reference art". Writing "silver hair" from a
   grayscale page is how you get a character who does not exist.
2. **Panel 3 is described as having no dialogue.** The sfx never becomes a line.
3. **"the child asks, then the adult pats"** — explicit order, because "then" alone is
   routinely flattened by the model.

---

## Acceptance: what to check and where it fails

```bash
python scripts/check_motion.py --input clip.mp4
ffmpeg -y -i clip.mp4 -vn -ac 1 -ar 16000 audio.wav
whisper audio.wav --language ja --output_format json --output_dir asr
python scripts/pitch_check.py --input audio.wav --segments "0-3,3-6,6-9"
```

| Check | Pass condition | Typical failure |
|---|---|---|
| Order | Actions match panel order | Pat happens before the question (C1/C16) |
| Speaker | Each line in the right voice | Character calls their own name (C4) |
| sfx | No voice on sound effects | Character says "pat pat" (C5) |
| Identity | Outfits match references | Mother and grown child merged (C7) |
| Color | Matches colored reference | Everyone becomes blonde (C9) |
| Timing | Speech fits the shot | Line spills past the cut (C10) |
| Stillness | Motion never fully stops | Padding with a frozen frame (C13) |
| texture delta | Read per shot, confirm by eye | Dense background trips the metric |

The last row matters: the `center_texture_delta` metric measures high-frequency texture
change in the center of frame. Point it at a cityscape and it screams at you with no
face on screen. Pull frames before believing it.

---

## What this walkthrough demonstrates

Every failure listed here is a **reading** failure, not a rendering failure. The video
model did what it was told. The instructions were wrong.

That is why the constraints come first and the rendering comes last.
