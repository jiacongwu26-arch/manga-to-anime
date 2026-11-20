# End-to-end walkthrough

Two pages, two characters: a child and an adult. Generic values; substitute your own.

The point of this walkthrough is not the output — it is **where the constraints fire**.
Every number below comes from running the scripts on
[`examples/page_plan.sample.json`](../examples/page_plan.sample.json).

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

The reviewed plan is five panels, not three: the parse above merged the stairs panel,
the book panel, and the pat panel. The full reviewed file is
`examples/page_plan.sample.json`; its page 1 is:

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
    {"content": "Child holds up a picture book, excited",
     "bubbles": [
       {"type": "speech", "speaker": "child",
        "text_ja": "大きくなったら冒険に出るんだ！",
        "text_ja_kana": "おおきくなったらぼうけんにでるんだ！"}
     ]},
    {"content": "Adult sits alone at the table, chin on hand, speaking gently",
     "bubbles": [
       {"type": "speech", "speaker": "adult",
        "text_ja": "あら、じゃあまずは練習を頑張らないとね。",
        "text_ja_kana": "あら、じゃあまずはれんしゅうをがんばらないとね。"}
     ]},
    {"content": "Child asks a follow-up; adult's back fills the left foreground",
     "bubbles": [
       {"type": "speech", "speaker": "child",
        "text_ja": "それで世界を旅できるの？",
        "text_ja_kana": "それでせかいをたびできるの？"}
     ]},
    {"content": "Adult closes her eyes and pats the child's head (no dialogue)",
     "bubbles": [
       {"type": "sfx", "speaker": null,
        "text_ja": "そっと撫でる", "text_ja_kana": "そっとなでる"}
     ]}
  ]}}
}
```

Two things the review changes beyond the four errors above:

- **Panel 3 contains only the adult.** The raw parse put the child's line there; a panel
  with one character cannot carry the other character's dialogue.
- **Panel 5 is `sfx`, speaker `null`.** No line, no voice — only a soft cloth sound.

---

## Page 2: where identity splits

Page 2 has three panels:

1. The adult crouches and pats the child's head — 「もちろんよ。」
2. Wide shot: sky, mountains, one small figure flying.
3. The grown child's back, on a broom — 「もうすぐ着くわね。」

A naive parse sees "long-haired woman" in panel 1 and "long-haired person on a broom"
in panel 3 and concludes they are the same character. They are not: panel 3 is the
**child, grown up**. Panel 1's adult is the mother.

The error produces "the mother flies off to the destination alone" — the protagonist
vanishes from her own story.

**How the review catches it**: compare clothing and accessories, not hair. A grown-up
version of a character keeps a signature accessory but not the same outfit. Different
outfit + different age = two identities until proven otherwise.

Second mistake on the same page: panel 2 (wide, one small figure) and panel 3 (back
view) are the same character at two scales. Do **not** turn them into two people. The
wide shot is an establishing beat, not a new cast member.

---

## Timing: the ledger that says no

Run:

```bash
python scripts/plan_duration.py --target 28 --unit 30 --segment 15,13 \
  < examples/page_plan.sample.json > plan.json
```

Actual shot list:

| Shot | Source | Type | Lines | mora | Duration |
|---|---|---|---|---:|---:|
| 1 | p01.p1 | dialogue | お母さん！ / どうしたの？ | 10 | 3.14s |
| 2 | p01.p1 | reaction | — | 0 | 2.00s |
| 3 | p01.p2 | dialogue | 大きくなったら冒険に出るんだ！ | 17 | 2.95s |
| 4 | p01.p3 | dialogue | あら、じゃあまずは練習を頑張らないとね。 | 20 | 3.26s |
| 5 | p01.p4 | dialogue | それで世界を旅できるの？ | 13 | 2.44s |
| 6 | p01.p5 | emotion | — (sfx) | 0 | 2.20s |
| 7 | p02.p1 | dialogue | もちろんよ。 | 5 | 1.20s |
| 8 | p02.p2 | establishing | — | 0 | 3.50s |
| 9 | p02.p3 | dialogue | もうすぐ着くわね。 | 8 | 1.54s |

Sum: **22.23s**. Target for a 28s cut: **5.77s short**.

Notes on the numbers:

- Shot 1 gets 0.8s for the beat *between* its two lines. Single-line panels get no
  inter-line beat — that was a bug in an earlier version.
- Shot 7's raw estimate is 1.11s, but the 1.2s single-shot floor applies, so 1.20s.
- Shot 6 is `emotion` because the panel content mentions closed eyes; its sfx produces
  no line.

Segments:

| Segment | Content | Actual | Limit |
|---|---|---:|---:|
| 1 | shots 1–5 | 13.79s | 15s |
| 2 | shots 6–9 | 8.44s | 13s |

The planner's actual output:

```
content is 22.2s < target 28.0s: add shots; do not stretch existing shots or pad with a still frame
segment 1 is 13.79s of 15.00s: 1.21s short; add a shot instead of stretching one
segment 2 is 8.44s of 13.00s: 4.56s short; add a shot instead of stretching one
```

Two wrong fixes and one right fix:

- Wrong: stretch shot 9 from 1.54s to 6s. The character stands still while the wind
  sound plays. C13.
- Wrong: freeze the last frame for the remaining seconds. C13 again, worse.
- Right: add shots — an insert of the picture book, a beat on the adult's expression,
  a wider establishing shot of the destination. Each is a real cut with its own content.

---

## Prompt: what the constraints turn into

```text
Convert this manga page into animation.

[References] 1 = official colored art of the child; 2 = official colored art of the adult;
             3 = manga page 1; 4 = manga page 2
[Character lock] follow the reference art for hair color, eye color, and costume.
                 Do not introduce any character not in the references.
                 The adult and the grown child are two different characters.
[Dialogue] all lines in Japanese. The child has a bright young voice, the adult a calm
           mature voice, the grown child a calm young voice. No BGM.
[Reading order] right to left, top to bottom.
  - P1-1: the child calls out, the adult answers.
  - P1-2: the child holds up a picture book.
  - P1-3: the adult alone at the table, chin on hand.
  - P1-4: the child asks a follow-up, the adult's back in the left foreground.
  - P1-5: the adult pats the child's head. No dialogue; only the soft sound of cloth.
  - P2-1: the adult crouches and answers.
  - P2-2: wide shot, sky and mountains, one small figure flying.
  - P2-3: the grown child's back on a broom.
[Timeline] 0-3s P1-1; 3-6s P1-2; 6-9s P1-3; 9-11s P1-4; 11-13s P1-5; ...
[Order] the child asks, then the adult pats. The adult answers, then the grown child flies.
[Output] no text, subtitles, speech bubbles, or panel borders in frame.
```

Three things to notice:

1. **No color values.** It says "follow the reference art". Writing "silver hair" from a
   grayscale page is how you get a character who does not exist.
2. **Panel P1-5 is described as having no dialogue.** The sfx never becomes a line.
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
| Identity | Outfits match references | Adult and grown child merged (C7) |
| Color | Matches colored reference | Everyone becomes blonde (C9) |
| Timing | Speech fits the shot | Line spills past the cut (C10) |
| Stillness | Motion never fully stops | Padding with a frozen frame (C13) |
| Texture delta | Read per shot, confirm by eye | Dense background trips the metric |

The last row matters: `center_texture_delta` measures high-frequency texture change in
the center of frame. Point it at a cityscape and it screams with no face on screen.
Pull frames before believing it.

---

## What this walkthrough demonstrates

Every failure listed here is a **reading** failure, not a rendering failure. The video
model did what it was told. The instructions were wrong.

That is why the constraints come first and the rendering comes last.
