# Duration estimation

## Japanese (default): mora timing

Do not estimate Japanese by character count. Count mora.

### Mora counting

- One kana = one mora
- Small kana ゃゅょぁぃぅぇぉ = 0
- っ, ん, ー = 1 each
- Kanji needs a kana reading (`text_ja_kana`); if the reading is missing, **refuse to estimate** rather than guess

### Formula

```
duration = mora count / speed * density + 0.4s (breath)
```

| Register | mora/sec |
|---|---|
| Calm / statement | 7.0 |
| Emotional / exclamation | 6.0 |
| Urgent / shouting | 8.5 |

Density: statement 1.0 | exclamation 0.9 | question 1.1 | trailing off 0.8 | proper nouns +0.2

### Worked example

| Line | mora | Estimate |
|---|---:|---:|
| お母さん！ | 5 | 1.15s |
| どうしたの？ | 5 | 1.19s |
| 大きくなったら冒険に出るんだ！ | 17 | 2.95s |
| あら、じゃあまずは練習を頑張らないとね。 | 20 | 3.26s |
| それで世界を旅できるの？ | 13 | 2.44s |
| もちろんよ。 | 5 | 1.11s |
| もうすぐ着くわね。 | 8 | 1.54s |
| **Total** | **73** | **13.64s** |

Seven lines take ~13.6s of dialogue. That leaves ~14s of non-dialogue for a 28s cut.

## Other languages

```
duration = characters / speed * density + 0.4s (breath)
```

| Register | chars/sec (Chinese) |
|---|---|
| Calm | 5.0 |
| Emotional | 4.0 |
| Urgent | 6.5 |

Use the language of the actual voice track. Do not apply the Chinese formula to Japanese or vice versa.

## No-dialogue baselines

| Panel type | Duration |
|---|---|
| Establishing / wide | 3.5s |
| Action | 2.5s |
| Emotion / close-up | 2.2s |
| Transition / small panel | 1.5s |
| Inner state / borderless | 3.0s |

## Gutter time

| Gutter type | Added time |
|---|---|
| Same moment | 0s (hard cut) |
| A few seconds later | +0.8s |
| Scene change | 0s (hard cut) |
| Day+ later | 0s (hard cut + transition marker) |

## Ledger check

```
required N = sum of all shot durations
target T = 30s planning unit, or 15+13 = 28s render total
```

### N > T

Compress in this order, **never touching dialogue shots**:

1. Transition / small panel: 1.5s → 1.2s
2. Reaction shot: 2.0s → 1.5s
3. Establishing shot: 3.5s → 2.5s
4. Still over → **stop and report**:
   - required N vs target T
   - what was compressed and how much was saved
   - two options: split into more segments, or delete named panels
   - **Never**: freeze the last frame, speed up speech, silently drop panels

### N < T

1. Add a shot (insert / establishing / reaction), do not stretch existing shots
2. Extend emotional or establishing shots only within their natural range (max 8s per shot)
3. Still short → report the gap; do not pad with a still frame

## Output timeline format

```json
{
  "total_seconds": 28.0,
  "unit_seconds": 30.0,
  "segment_spec": [15.0, 13.0],
  "segments_count": 2,
  "segments": [
    {"segment": 1, "start_s": 0.0, "end_s": 15.0, "duration_s": 15.0, "limit_s": 15.0,
     "shots": [{"shot": 1, "type": "establishing", "duration_s": 3.5, "start_s": 0.0, "end_s": 3.5}]}
  ],
  "shots": []
}
```

## Hard constraints

- Dialogue shot lower bound = dialogue duration × 0.95 (do not speed up speech more than 5%)
- Single shot upper bound 8s (split longer ones)
- Single shot lower bound 1.2s (shorter is unreadable)
- Total tolerance ±0.5s
- Segment length must equal the render duration requested from the API; shots must not straddle a segment boundary
