# Reading order and panel semantics

## Base reading order

Standard Japanese manga: **right to left, top to bottom**.

- Same row: right panel first
- Same column: top panel first
- Exceptions: vertical webtoon (single column, top to bottom), Western comics / picture scrolls (left to right) — decide from the material, do not assume manga order

## Island grouping

Panels that read as one continuous moment = one island.

- Within an island: continuous action, continuous time, same space
- Across islands: scene change, time skip, entering/leaving a flashback
- **Animation meaning**: hard cuts within an island; island boundaries are the scene-change points

## Frame types

| Type | Meaning | Animation treatment |
|---|---|---|
| Standard frame | Normal narrative | Normal shot |
| Borderless / open | Inner state, spatial expansion | Long take, depth of field, slow push |
| Bleed (extends past page edge) | Impact, big scene | Establishing shot or emotional beat |
| Slanted frame | Turmoil, tension | Handheld feel, quick cuts |
| Inset panel | Inserted detail or memory | Insert close-up |

## Output format

```json
{
  "reading_order": "right-to-left",
  "islands": [{"island_id": 1, "frame_range": [1, 3], "scene": "interior"}],
  "panels": [
    {"panel": 1, "bbox_xyxy": [x0, y0, x1, y1], "reading_rank": 1,
     "island_id": 1, "frame_type": "normal",
     "content": "description"}
  ]
}
```

## Common misreads

- Treating two side-by-side panels as sequential (right comes first)
- Treating an inset panel as an independent narrative panel (it is an insert)
- Skipping borderless panels as "not a panel" (they are often the most important emotional beats)
- Treating a two-page spread as two independent pages (it is one continuous image)
