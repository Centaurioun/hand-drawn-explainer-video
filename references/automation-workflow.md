# Complete Video Production Workflow

## 1. Establish inputs and reusable assets

Inspect the original script, complete narration, sample feedback, character/color references, output directory, and tools. Follow [preflight and recovery](preflight-and-recovery.md) to test the chosen route, separately checking rendering requirements and optional independent speech review. Reuse verified local configuration and existing approvals; do not request approval for every shot. Record script and pronunciation changes.

Retain script.txt (original), narration.txt (synthesis input, with documented pronunciation adjustments), assets/, DESIGN.md, timeline.json, index.html, render logs, and inspection reports in the requested project directory.

Maintain a concise project status file with script digest, narration source, sample approval scope, asset/animation/inspection status per scene, and latest successful render. Resume at the affected stage: typography or color changes do not require new narration; spoken changes require corresponding audio edits and realignment of affected subtitles and later shots. Never log credentials or raw request headers.

## 2. Narration before timing

Follow [voiceover](voiceover.md). Actual audio determines duration. Shots often last 4–6 seconds, but this is not mandatory. Respect duration limits through authorized script or moderate speech-rate adjustments, never by cutting the final sentence.

Store at least these fields, in seconds:

```json
{
  "duration": 36.0,
  "audio_duration": 34.848,
  "narration_text": "Complete original script, matching the concatenated captions",
  "alignment": "sentence_pause_estimate",
  "scenes": [
    {"n": 1, "start": 0.0, "end": 4.0, "caption": "Corresponding original text"}
  ]
}
```

This is a schema illustration, not complete valid production data. Replace placeholders with the actual full script and every shot. Document differences between subtitles and synthesis input; never silently replace the original with ASR errors.

## 3. Plan visuals

For each shot record start/end, narration, type (character scene/knowledge graphic/real asset), final composition, successive changes, transition, sources, and verification needs. Do not force three changes merely to meet a quota. Visuals should appear when their concepts are narrated.

Characters introduce questions, experiences, and reminders; diagrams explain processes, relationships, and comparisons. Use real assets for screen demonstrations and factual screenshots. One new picture per sentence does not ensure explanatory quality.

Confirm route using the main skill. For genuine drawing, use [stroke-story-workflow.md](stroke-story-workflow.md) and plan shared canvas, semantic regions, and start times rather than independent SVG scenes. Use the remaining HyperFrames rules only for programmatic elements.

## 4. Create controllable assets and motion

Use the installed HyperFrames skill when available and read its authoring, CLI, and animation guidance. Report missing runtime capabilities; installed skill files alone do not establish readiness.

Copy examples/program-animation/skill-demo/ into a new project as a reference for independent arms, sequential bubbles, cards assembling into a book, processes, materials, reuse arrows, closed permission locks, and magnifying-glass checks. Run npm install for pinned dependencies; new topics need new scripts and semantic relationships, not merely a new title.

- Use local assets and GSAP; declare fonts explicitly, with local() in @font-face where appropriate. Disclose dependencies or embed licensed fonts for portability.
- Fix outer SVG coordinates; animate named inner groups to avoid misplaced limbs.
- Hide future scenes using explicit CSS ID rules, not only paused timeline set() calls at t=0.
- Replace the original arm with its animated counterpart; avoid duplicate limbs and accidental occlusion by objects.
- Do not animate the same property from multiple timelines; use finite repeats, deterministic timelines, and required synchronization registration.
- Lay out longest titles, captions, and simultaneously visible elements before adding entrances. Inspect legitimate transition overlaps rather than ignoring all collisions.
- Leave adequate final reading time; no sudden return to the first frame or black screen.

Use video models only for genuinely complex natural motion. Existing generated images may need layer separation, inpainting, regeneration, or SVG conversion; explain texture changes. Do not request approval again for already approved simplified art.

## 5. Environment and rendering

Verify Node, complete working FFmpeg/FFprobe, and browser; check versions, audio probing, and H.264 encoding before long renders. HyperFrames 0.8.20 was verified upstream; pin a version based on the current CLI help rather than upgrading existing projects indiscriminately. Initialize with official CLI, preserve project instructions, and distinguish failed remote skill downloads from local plugin readiness.

Some editor-bundled FFmpeg builds decode but lack libx264/crf; copied shared executables may lack DLLs. Use complete distributions or a verified imageio_ffmpeg.get_ffmpeg_exe(); the latter may require separate FFprobe. Set HYPERFRAMES_FFMPEG_PATH and HYPERFRAMES_FFPROBE_PATH at process scope, not global PATH. Cached browser paths are not portable.

Check representative scenes, longest captions, and transitions; run current CLI check or equivalent lint/validate/inspect. Fix issues, render a 3–5-second internal sample, then export the full MP4. Start with two rendering workers and adjust to resources. Save logs and report substantive progress. Encoding failures require environment fixes or rerendering, not repeated TTS or image requests.

## 6. Verify and deliver

Follow [quality-and-delivery.md](quality-and-delivery.md). Deliver only a sample when requested; after sample approval for a full video, continue to completion. A full video includes the playable output, editable project, and audio; users should not have to export it themselves.
