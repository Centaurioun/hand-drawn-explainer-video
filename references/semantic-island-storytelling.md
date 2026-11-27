# Semantic-Island Storytelling: Draw and Narrate in Stages

Use for left-to-right, gradual storytelling with keywords, numbers, or short labels. This is not a grid of cards: two independent narrative events share a canvas. The first is inked, colored, and held, then the second begins while earlier content remains.

## When to use

- Clear two-stage relationship: cause/result, past/later, person/product.
- Each stage forms a coherent small scene with natural spatial relationships on a landscape canvas.
- Narration allows about 2.5–4 seconds of visible drawing per stage.

Do not force islands: one action or event uses a complete single scene; three or more independent events usually need separate scenes. Process cards and relationship diagrams use programmatic animation.

## 1. Budget audio before art complexity

hand-follow smooths hand display, not ink speed. Actual readability depends on available region duration ÷ line and color-block complexity. Obtain real audio and allocate time for:
1. Ink and main contours.
2. Limited flat colors.
3. Finished-image hold, preferably at least 0.5 seconds.
4. Optional keyword reveal.

If the sample looks rushed at normal speed, lengthen or redistribute narration time, simplify tiny components/hatching/texture, reduce region content, or move content to another scene. Do not merely lower hand-follow or frame rate. Simplify circuitry pins, wood grain, page text, pseudo-screen text, crowd faces, dense shadows, and repeated decorative lines.

## 2. Dual-island image constraints

For 16:9, start with similarly scaled complete left/right narrative islands, a 6–10% blank vertical gutter, bottom 18% subtitle safe zone, and no connecting floor lines, wires, table edges, shadows, arrows, ribbons, or contours. Use white/warm-white paper, clear dark ink, limited flat color, low texture. No generated text, dates, company names, logos, screen contents, or exact product names.

```text
Landscape 16:9 hand-drawn story illustration on a single sheet with two
independent but narratively continuous islands.
Left: [first-stage characters, actions, essential props].
Right: [second-stage characters, actions, essential props].
Keep a clean 6–10% vertical gutter, with no crossing floor lines, wires,
table edges, shadows, arrows, or contours. Reserve bottom 18% for subtitles.
Natural-skin-tone chibi characters, clean ink, limited flat color, low texture,
few accents. No text, numbers, logos, pseudo-writing, dense hatching,
tiny parts, or photorealistic textures.
```

Save and inspect each generated image immediately. Prefer sequential generation to avoid ambiguous partial failures and repeated charges. Fix only the current image when pseudo-text, age mismatch, or dense lines appear.

## 3. Annotation and timing

At least one semantic region per island. Put boundaries in gutters; do not cut faces, hands, or props. Run check_drawable_regions.py and fix overlaps, crossing foreground lines, and insufficient spacing.

```text
Left ink → left color → left hold → optional left keyword
→ right ink → right color → right hold → optional right keyword
```

The right island stays fully hidden until its start; left remains visible afterward. protectedRegions handles minor unavoidable occlusion, not structurally connected islands.

## 4. Keywords

Use deterministic ASS/HTML text layers, not generated image text. Choose short keywords or accurate product names in the gutter, upper space, or near completed islands. Reveal letters progressively or with a short mark; avoid covering people with headlines. ASS `\kf` or equivalent typing reveal should align with narration, avoid expressions, subtitle zones, and the next drawing region.

## 5. Starting parameters and sample

For sparse 16:9 dual islands with low-texture chibi art:

```text
--ink-path skeleton --color-fill contour-wipe
--hand-follow 0.25 to 0.30
--hand-height 220 to 260
```

Ranges are sample starting points, not global defaults or literal CLI range syntax. Play an 8–12-second representative two-island shot continuously; inspect first completion, second start, large turns, coloring, and keyword reveals before batch rendering.

## 6. Story rhythm

Prefer verifiable conflict/question hook → origin → turning point → result/value. A hook is not an exaggerated headline. If time permits, use up to 60 seconds to make key events readable rather than rushing everything into 20 seconds.

## 7. Required frame checks

In addition to contact sheets, inspect about 0.2 seconds before each island completes, about 0.2 seconds after the next begins, three frames on either side of each scene cut, final 0.3–0.5 seconds, and middle/completed keyword reveals.

Automated checks cannot detect abrupt enlarged source overlays, premature island leakage, or face-covering keywords. Inspect actual frames, not just exit codes.
