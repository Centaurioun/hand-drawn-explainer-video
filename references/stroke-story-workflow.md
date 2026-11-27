# Stroke-by-Stroke Storytelling

Use when the user wants a picture drawn progressively while narration plays. The defining feature is continuous ink on one persistent canvas, following narrative meaning. Earlier art remains while later characters, actions, and outcomes are added.

## Backend and capabilities

Use the runtime in vendor/srt-whiteboard-animation/. It is not a second skill and introduces no independent trigger or extra approval. First run its scripts/prepare_env.py to create an isolated environment, then run read-only preflight:

```text
<python> <skill>/scripts/stroke_story_preflight.py \
  --report <project>/preflight-stroke-story.json
```

Preflight installs nothing, calls no models, and synthesizes no speech. Failure blocks only stroke rendering; preserve approved narration, SRT, and illustration. Do not silently fall back to SVG; report the gap and obtain approval.

The region masks, persistent canvas, and stream renderer derive from MIT-licensed https://github.com/geeklee/srt-whiteboard-animation. The bundled snapshot produces video tracks; the main skill handles narration, subtitles, final composition, and acceptance. See vendor/srt-whiteboard-animation/UPSTREAM.md and its preserved license. Consult [upstream review](upstream-whiteboard-review.md) before adopting experimental changes.

## 1. Audio and timing

Reuse or create full narration before generating SRT aligned to real audio. SRT determines drawing rhythm, not automatically burned-in captions. Retain script.txt (original), narration.txt (synthesis input), narration.mp3 (approved voice), captions.srt, and timeline.json (sentence, scene, and composition timing).

Use the user-selected or configured language-compatible voice. Do not charge again for matching approved audio. For drawing and narrating in stages, left-to-right composition, or keywords during drawing, read [semantic-island-storytelling.md](semantic-island-storytelling.md). Allocate ink, coloring, and hold from real audio before choosing illustration complexity.

## 2. Design drawable complete scenes

Write DESIGN.md and per-scene illustration plans. One continuously completed scene can support 20–35 seconds; for multiple events or changing relationships prefer 4–8-second coherent scenes. If one image makes characters tiny, crowds five or more regions, or requires sticker-like framing, split it.

Source art uses 9:16, 4:3, or 16:9 appropriate to platform and narrative space; keep subjects clear of headings and subtitles. Use clear dark contours, limited flat color, low texture, ample space. Chibi proportions are acceptable with consistent features, clothes, and period props. Render long text, dates, laws, logos, and names deterministically afterward. Avoid crayon noise, halftones, dense hatching, photographic texture, and large dark fills misidentified as ink.

Inspect images before annotating; never guess coordinates from scripts or mechanically sort left-to-right.

### 2.1 Choose aspect ratio and narrative composition

Connected lines crossing time regions cause unfinished objects and jumps. Do not default to four blocks.

- Unless portrait is required, use 16:9 for group scenes, historical environments, and spatial stories; 4:3 suits centered book-like scenes, 9:16 a single subject or portrait publication.
- Multi-event scripts over 20 seconds generally need continuous 4–8-second scenes.
- Each complete scene can have natural contact and occlusion. Draw as one region or at most environment then subject.
- Keep characters, paper, palette, and camera direction consistent across scenes instead of creating grids or sticker collages.
- Use 2–4 semantic islands only for explicitly requested progressive multi-meaning canvases or genuinely separate events sharing one illustration. Leave about 5–8% width as a natural gutter and avoid connecting contours or backgrounds.
- Render precise wording and laws in subtitles/post-production rather than generated art.

Describe one event, relationships, environment, and camera per image prompt. Add island count and gutters only when applicable. Inspect actual images; if framing makes art a grid or catalog, split and regenerate. Prefer sequential generation, saving and inspecting each result to avoid uncertain partial failures and duplicate charges.

### 2.2 Drawability check

For two or more independent regions, run after annotation and before the preview editor:

```text
<backend-python> <skill>/scripts/check_drawable_regions.py \
  <image> <annotation.json> --report <project>/drawable-regions-report.json
```

Check bounds, rectangle overlap, spacing, and connected foreground crossing multiple regions. On failure prefer separate complete scenes, then repair source art. Minor paper-texture false positives require documented human review. One full-image region needs no artificial gutter. Passing is not a substitute for sequential playback.

## 3. Annotate by narrative meaning

Create a matching annotation JSON. Each region corresponds to one spoken event: setup → key person/object → conflict/rule → reaction/result.

- sequence: narrative order.
- subtitle: corresponding original phrase.
- startMs/durationMs: real audio.
- region: visible subjects for that event.
- protectedRegions: safeguard not-yet-started subjects in unavoidable overlaps.

Completed regions remain on the same canvas. Preview future-region invisibility and avoid cutting faces, hands, or props. Place region boundaries in gutters; protectedRegions is not a cure for strongly connected or unsuitable compositions.

Before rendering, run backend scripts/annotation_schema.py <annotation.json>. Out-of-bounds coordinates, canvas mismatch, or missing timing are blocking errors; nonconsecutive sequences, overlapping windows, and short holds need review.

## 4. Rendering choices

Default representative settings:

```text
--ink-path skeleton --color-fill contour-wipe --hand-follow 0.35
```

skeleton follows extracted main ink paths; grid is for solid text or unstable skeletons and can look blocky. contour-wipe is contour-aware coloring, not actual human coloring order.

hand-follow controls the displayed hand's pursuit of the tip: 1.0 is immediate, 0.35 eases motion for group scenes/coloring. It changes hand position only, not narration, ink strokes, or scene duration.

If real ink remains too fast, increase time, divide an event, or simplify circuitry, wood grain, pseudo-writing, hatching, and decorations. At normal 30fps, main contours, colors, and a minimum 0.5-second hold must be readable.

Hand size is independent of smoothing. For complex 16:9 groups compare --hand-height 260 to 340; portrait single subjects can use larger hands. Avoid obscuring faces and newly drawn props; preserve approved defaults unless explicitly changed.

An empty allowed mask must preserve the current canvas through its entire original window, without a fake centered hand or early subsequent regions. Review annotation rather than deleting the region.

Play a representative sample continuously through at least one pen lift, broad turn, and color fill. Adjust hand-follow within 0.25–0.55 if needed; smaller values are smoother but lag more. Do not lower frame rate to conceal speed. Use --bare-tip only when requested.

Render 10–15 seconds including at least two regions, one pen lift, and one color completion. When sample approval is requested, deliver only the sample; after approval reuse audio, style, canvas rules, and backend settings.

## 5. Final composition

The backend produces visual tracks. Use the main workflow to add narration and deterministic subtitles to final MP4. HyperFrames/FFmpeg handle captions, titles, transitions, and composition, not replacing the drawn subject.

Preserve accurate subtitles, laws, and names. Add short keywords after drawing, using ASS `\kf` or equivalent deterministic reveal, without covering expressions, subtitle zones, or future regions.

### 5.1 Complex color completion

contour-wipe works well on low-texture flat art but may leave white patches in paper texture, pale clothes, and complex groups. Compare each scene's final 0.3–0.5 seconds to approved art.

Only if confirmed incomplete, retain the entire stroke process and fade in the approved source starting about 0.9 seconds before the end, with a 0.65-second fade and reading hold. If complete, re-encode and join directly. Unconditional overlays risk crops, scaling, and flashes. Never regenerate approved illustration or hide errors with hard cuts.

Use the finalization helper with paths relative to manifest:

```json
{
  "width": 1920,
  "height": 1080,
  "fps": 30,
  "narration": "assets/narration.mp3",
  "ass": "render/captions-and-titles.ass",
  "scenes": [
    {"video": "render/scene-01.mp4", "image": "assets/scene-01.png", "durationMs": 7400}
  ]
}
```

```text
<python> <skill>/scripts/finalize_stroke_video.py \
  --manifest <project>/stroke-finalize.json \
  --ffmpeg <preflight-verified-ffmpeg> \
  --source-overlay never \
  --output <project>/final.mp4
```

By default the script does not overlay finished scenes; it standardizes frame rate, dimensions, time base and adds narration/ASS. Only use --source-overlay always after verifying missing color; provide approved images in manifest. This avoids concat/PyAV timestamp rounding errors. Omit narration or ass fields when unnecessary.

Use simple cuts or light fades to preserve continuity. Experimental eraser transitions add a large hand and extra movement; test before selecting, record extra duration in timeline.json and shift captions/audio.

## 6. Acceptance

In addition to common QA:
1. Clean first frame without future lines.
2. New ink near pen tip; pen lifts without fake connecting lines.
3. sequence and startMs match narrative.
4. Completed areas persist; future regions remain hidden.
5. Final frame matches approved color source, with at least 0.5 seconds hold.
6. Hand smoothing does not obscure content or visibly detach from new strokes.
7. No texture-driven scribbling, teleports, white patches, or dark flashes.
8. No duplicate/black frames or timestamp jumps after merging.
9. Final MP4 contains complete requested video, narration, captions, duration, final sentence, and frame.
10. For multiple regions inspect ~0.2 seconds before completion and ~0.2 seconds after next start, three frames on either side of cuts, and final 0.3–0.5 seconds.

Retain source art, annotation JSON, SRT, narration, scene tracks, final project, and reports to support partial rerenders and rollback.
