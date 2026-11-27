# Reference Images, Style Selection, and Example Maintenance

Read when users provide references, change styles, ask what exists, or request example updates. A single video request does not authorize changing future defaults.

## Actual available assets

| Reference | Documentation | Available | Not available |
|---|---|---|---|
| Programmatic animation | [Demo](../examples/program-animation/skill-demo/README.md) | SVG/HTML/GSAP project, audio, timeline, PNG, 14-second MP4 | Public full 36-second MP4 |
| Multi-scene stroke story | [Three Articles of Law](../examples/stroke-story/yuefa-sanzhang/README.md) | 16:9 smoothed-hand MP4, seven-scene contact sheets, timeline, report, editable archive | Generic historical-character template |
| Dual-island stroke story | [Steve Jobs](../examples/stroke-story/steve-jobs/README.md) | Approved 16:9 art, two-region annotation, preview, 8.9-second sample | Universal character/story/duration template |
| Q Doodle crayon | [Style guide](style-guide.md) | Line, color, proportion, composition, and Flow motion instructions | Example image, asset pack, verified project |

No prebuilt multi-style gallery exists. Update the table and skill asset status only when real new assets exist.

## Working from references

Inspect actual reference images; ask for an accessible image if missing. Distinguish style reference, specific-character preservation, and animation of the supplied image itself. Do not ask if the request already resolves this.

In DESIGN.md separately record visual style (source, line quality, colors, background, proportions, character anchors, spacing), motion (example or new reveal sequence, strokes, joints, pacing, transitions), and approved voice. A still image does not establish original animation behavior. Changing style does not change voice or regenerate matching narration.

Choose suitable technology: vectors allow independent motion but cannot pretend to preserve crayon texture exactly; raster images may need layering, inpainting occlusions, or multiple poses. Natural continuous motion may require image-to-video services; verify access and costs. Use available generation tools with their reference-image requirements; prompts are not finished videos.

Create a representative still and short animation to check consistency, strokes, subtitle safety, and motion. No promise of arbitrary poses or pixel-perfect consistency from one reference. Deliver sample only when requested; for an authorized full video continue after internal checks unless essential decisions are missing.

## Improving examples

1. Determine whether the change affects only this video, updates the default, or adds an optional style. Do not replace defaults for local changes or additions.
2. Preserve a rollback copy and input/version/digest in the workspace. Never overwrite the only approved example first.
3. Retain actual reference/representative images, editable source, DESIGN.md, and playable sample; document elements, timing, transitions, and missing assets.
4. Render a new short sample, check motion/transitions/subtitles and regressions; follow [preflight](preflight-and-recovery.md) and [quality](quality-and-delivery.md).
5. Install into the skill only when explicitly authorized to update defaults/save a preset. New styles may have named asset directories and reference rules; do not create empty placeholders.
6. Synchronize index, SKILL.md, and preferences.json only as needed. Change description and agents/openai.yaml only for new selectable capabilities. Replace superseded rules rather than accumulating contradictory patches.
7. Verify relative links, skill structure, installed files, and tested version; deliver previews and rollback package, distinguishing runnable styles from specification-only styles.

Description summarizes capabilities and use cases, not versions or changelogs. Inspect actual installed assets to assess updates.
