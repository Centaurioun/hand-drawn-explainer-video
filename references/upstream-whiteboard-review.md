# srt-whiteboard-animation Upstream Review

Reviewed https://github.com/geeklee/srt-whiteboard-animation and its unmerged PR #4. The upstream code is MIT licensed; retain license and attribution when copying. This record avoids repeated research and treating experimental behavior as stable defaults.

## Adopted

- Subtitle-driven sequence/startMs/protectedRegions scheduling.
- Persistent canvas, regional stream paths, ink then color.
- Annotation preflight for dimensions, coordinates, protected regions, timing, and holds.
- Empty allowed masks retain the original time window so later art does not appear early.
- Separate --hand-height and --hand-follow for occlusion and hand motion.
- Re-encoding to uniform dimensions, frame rate, and time base before joining, implemented in finalize_stroke_video.py.

## Replaced with local approaches

- Rather than edge-tts per SRT cue, preserve user-selected whole narration and real timing; do not accelerate speech to fit short drawing windows.
- Rather than default 25–35-second single canvases, prefer 4–8-second landscape scenes for multi-event stories.
- Rather than silent merging alone, finalization also supports approved source completion, narration, ASS subtitles, and consistent time base.

## Not defaults

Xiaohei/minimal line art only when chosen; no overriding approved natural-skin-tone chibi art. Titles and 2–4 handwritten points are optional for educational work, not mandatory for historical stories. Covers only when needed. Test eraser transitions because an extra large hand can disrupt narrative. Extend visuals or revise shot planning rather than automatically compressing approved speech into subtitle windows.

## Future updates

Distinguish upstream main from unmerged PRs. Adopt only mechanisms verified by real samples without altering approved style or narration. Test annotation errors, empty masks, complex group scenes, multi-scene merging, and final audiovisual output before changing defaults.
