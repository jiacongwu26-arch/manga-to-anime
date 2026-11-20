# API integration

This skill is provider-agnostic. The request shapes below match MiniMax H3-style
"multimodal content array" APIs; adapt field names to your provider.

## Submit

```http
POST {BASE_URL}/video_generation
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

```json
{
  "model": "MiniMax-H3",
  "resolution": "480p",
  "duration": 15,
  "ratio": "16:9",
  "content": [
    {"type": "text", "text": "<prompt>"},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<character ref>"}, "role": "reference_image"},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<manga page>"}, "role": "reference_image"},
    {"type": "video_url", "video_url": {"url": "https://.../prev_segment_tail.mp4"}, "role": "reference_video"}
  ]
}
```

### Content roles

| Purpose | Type | role |
|---|---|---|
| Opening frame | `image_url` | `first_frame` |
| Closing frame | `image_url` | `last_frame` |
| Appearance / scene reference | `image_url` | `reference_image` |
| Motion / camera reference | `video_url` | `reference_video` |
| Voice / rhythm reference | `audio_url` | `reference_audio` |
| Regenerate from original | `video_url` | `base_video` |

**Constraint to check per provider:** `first_frame` / `last_frame` are mutually
exclusive with `reference_*` roles on some providers. Do not build a pipeline that
needs both at once. Verify against the provider's docs before spending.

### Field notes

- `content` must be an array; text items use `{"type":"text","text":...}`.
- `duration` is integer seconds within the provider's range (commonly 4–30, some
  models cap at 15). `resolution` is an enum (`480p|768P|1080p|2K` on H3-style APIs).
- Multiple `reference_image` items are accepted. Put the character reference first,
  then the manga pages in reading order.
- `reference_video` is billed like output seconds on some providers. Check pricing
  before enabling it on every segment.

## Query / download

```http
GET {BASE_URL}/query/video_generation
Authorization: Bearer {API_KEY}
```

- Returns an `items` array — **not filtered by task id**. Filter by `id` client-side.
- `status`: `running` → `succeeded`; on success take `content.url`.
- Keep polling on a fixed interval; do not re-submit on timeout.

## Client discipline

- Persist `task_id` before polling. A POST timeout means "submission state unknown":
  query the original task, never re-POST.
- Poll on a fixed interval; a polling budget expiring does not mean the server stopped.
- On failure or missing URL, do not silently retry with a different resolution.
- On Windows, `python` may be a Store stub; use the `py` launcher.
- When the payload contains base64 images, write the JSON to a temp file and
  `curl -d @file`; command-line length limits will bite otherwise.

## 30s planning / 15+13 rendering

Plan in a 30s ledger, render as two segments:

| Segment | Duration | Inputs |
|---|---|---|
| 1 | 15s | character refs + manga page(s) |
| 2 | 13s | character refs + manga page(s) + **segment 1 tail 2s as `reference_video`** |

- Keep camera language consistent across the boundary; the reference video carries
  motion, not identity — identity still comes from `reference_image`.
- Cut at a shot boundary so the seam lands between camera moves.
- Both segments must use the same character references, or the face drifts.
- If the provider rejects `reference_video` together with `reference_image`, do **not**
  silently switch to `first_frame` (that drops the identity reference). Keep the
  character references, carry continuity with identical camera language and a prompt
  that restates the pose, and record the limitation in the output report.

## Prompt skeleton

```
<Language of the dialogue>: convert this manga into animation.
[References] 1=character A; 2=character B; 3/4=manga pages in order; 5=previous segment motion
[Character lock] hair color / eye color / costume; forbid wrong colors; forbid new characters
[Dialogue] language, voice per character, ambience; no BGM
[Reading order] right to left, top to bottom; speaker per panel
[Timeline] beat-by-beat, with explicit order (A then B)
[Output] resolution, fps, duration; no text, subtitles, bubbles, panel borders
```

Write the dialogue in the language you want spoken. Video models generally follow
the language of the script; asking for a language different from the script often
fails.

## Cost discipline

- Model video is billed per output second. Short clips for iteration are not free.
- Confirm price per second and any long-video multiplier before submitting.
- Failed generations usually are not refunded: validate prompt, images, duration
  before submitting.
- Prefer one longer segment over many tiny ones for consistency; prefer two
  mid-length segments over one long one for cost — measure both, then decide.
