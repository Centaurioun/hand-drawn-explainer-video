# Verification and Delivery

Confirm capabilities actually work using [preflight and recovery](preflight-and-recovery.md). Check animation-map dependencies separately from the CLI. Share fixed text across transitions and fix normal collisions before long renders.

## Verify at distinct levels

1. **Text:** Compare original and captions section by section; preserve qualifiers and numbers. Store pronunciation adjustments separately. Explain intentional differences between spoken and displayed text.
2. **Project:** Run the current HyperFrames checks and fix scripts, fonts, hidden scenes, out-of-frame elements, and animation conflicts. Inspect transition warnings individually; do not suppress normal collisions.
3. **Rendered video:** Fully decode video and audio. Check duration, frame rate, dimensions, audio peaks, and ending. Inspect at least one frame per scene plus action peaks, transitions, and final frame. Contact sheets cannot replace necessary playback/listening.
4. **Actions and content:** Verify independent character/object movement, narrative reading order, closed locks, no extra/missing limbs, unintended occlusions, or malformed text. A moving progress bar does not prove subject animation works.

For stroke storytelling check clean initial frame, pen near new ink, natural turns and pen lifts, no leakage from future/protected regions, and persistence of completed regions. Compare the final 0.3–0.5 seconds of each scene to approved source art, looking for white patches from pale clothing or paper texture. For two or more semantic regions, inspect about 0.2 seconds before one ends and 0.2 seconds after the next begins. Inspect mid-reveal and completed keyword frames for face/subtitle collisions. contour-wipe is contour-aware coloring, not recovered human brush order.

For multi-scene output inspect at least three frames on each side of every cut and the final 0.3–0.5 seconds. Look for black/duplicate frames, timestamp regressions, and abrupt crop/zoom overlays. If lossless concat or PyAV merging fails, use finalize_stroke_video.py to re-encode with common frame rate, dimensions, and time base. Default --source-overlay never; explicitly opt in only when final-frame comparison confirms missing color.

Some project screenshot tools cover only a few timestamps per run. Verify actual screenshot counts and batch if needed. Automated contact sheets capture only one time per scene; inspect entrances, exits, action peaks, and endings separately.

## Reusable checker

```text
python <skill>/scripts/media_check.py --video final.mp4 --timeline timeline.json --report verification.json --contact-sheet contact.jpg --width 1080 --height 1920 --fps 30
```

Requires PyAV and NumPy; Pillow for contact sheets. Use an isolated environment. timeline.json follows the automation workflow schema; narration_text enables caption concatenation checks. Without original text report content as unverified, not passed.

The checker inspects real files, frame counts, audio values, timeline coverage, and motion statistics. Specify actual dimensions/fps. Default motion ROI excludes top 23% and bottom 26%; use --motion-roi X0 Y0 X1 Y1 for normalized custom bounds. Motion statistics cannot distinguish whole-image pans from character motion; low motion is a warning. Accurately record alignment. The checker does not perform ASR or prove semantic synchronization or aesthetics. Exit 0 only indicates no automated errors; warnings and human checks remain.

It cannot detect premature island leakage, face-covering keywords, or disproportionate end overlays; inspect real boundary frames. Use --timeline-only for offline timeline/content checks without rendering or paid calls.

## Deliverables

Final MP4, SRT, original script, separate narration, optional cover, timeline JSON, editable project ZIP, concise production notes and verification report. Sample-only tasks need not include the whole project. Editable means source project retained, not editable in an ordinary player.

ZIPs must contain required assets with relative references, no secrets, absolute user paths, or temporary files; disclose external fonts and runtime dependencies. Reuse approved narration without duplicate charges; distinguish requests from actual billing.

Link the real MP4 at the requested output path. Report actual duration, dimensions, completed scope, and limitations; never label a partial sample a complete video.
