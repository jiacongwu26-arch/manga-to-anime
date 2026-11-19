# Bubble taxonomy

## Six types

| Type | Visual cue | Meaning | Animation | Voice |
|---|---|---|---|---|
| speech | Oval/rounded box with a tail pointing at the speaker | Words spoken aloud | Mouth moves | Character voice |
| thought | Cloud/bumpy edge with dotted tail | Inner monologue | **Mouth closed** | Voice-over or silent |
| narration | Rectangular box, no tail, near page edge | Narrator text | No mouth movement | Narrator voice (flat) |
| shout | Jagged / burst edge | Shouted aloud | Mouth + bigger motion | Character voice, louder |
| sfx | Hand-lettered, no border, drawn over art | Sound effect | **Not dialogue** | Sound effect, no voice |
| phone | Boxy with teeth/antenna marks | Phone, broadcast, machine | Voice-over | Character voice + filter |

## Decision priority

1. Has a tail pointing at a specific character → speech
2. No tail, regular box shape → narration
3. Hand-lettered, no border → sfx
4. Cloud edge → thought
5. Jagged edge → shout
6. Boxy with teeth → phone

## Output format

```json
{"type": "speech|thought|narration|shout|sfx|phone",
 "speaker": "charA|unknown|narrator",
 "text": "original line or null",
 "text_ja": "Japanese line",
 "text_ja_kana": "kana reading",
 "bbox_xyxy": [x0, y0, x1, y1]}
```

## Common misreads

- **SFX read as dialogue**: hand-lettered "thump", "rustle" etc. is a sound, not a line. Voicing it is a disaster.
- **Narration read as dialogue**: narration boxes have no tail; voicing them with a character voice makes the character sound like they are talking to themselves.
- **Thought read as speech**: thought bubbles mean the mouth does not move; voicing them as speech breaks the shot.
- **Tail direction misread**: the tail points at the speaker; if it sits between two characters mark `unknown` instead of guessing.

## When unsure

- Unreadable text → `text: null`, do not guess
- Unknown speaker → `speaker: "unknown"`
- Ambiguous type → decide by the animation question: does the mouth move? yes → speech, no → thought/narration
