---
name: hand-drawn-explainer-video-nikola
description: Create, revise, and validate hand-drawn educational explainer videos, delivering narration, subtitles, timelines, editable projects, and real MP4 files. Supports two distinct production routes: stroke-by-stroke storytelling on a persistent canvas and programmatic animation of process cards, relationships, and diagrams using SVG/HTML/GSAP. Stroke stories support natural-skin-tone chibi characters, Xiaohei style, or other hand-drawn styles in single scenes, multi-scene stories, or two semantic islands. Use when users request drawing while narrating, stroke-by-stroke whiteboard animation, left-to-right drawing, educational animation, or conversion of scripts, SRT files, or biographies into hand-drawn videos. Also supports prompt-only delivery for image and video generation. Not intended for photorealistic avatars or unverifiable claims of completed videos.
---

# Nikola Hand-Drawn Explainer Video

Turn a topic, script, or SRT into a playable, inspectable, editable hand-drawn explainer video. Distinguish genuine stroke-by-stroke drawing from independently moving hand-drawn elements; never substitute one for the other without disclosure.

Prompt-only mode has no local media dependencies. The bundled stroke renderer requires an isolated Python environment on first use. Programmatic animation requires Node.js, HyperFrames, a browser, and FFmpeg. The existing default narration preset is Volcengine's Liu Fei voice; it requires the user's authorized account or a matching existing recording. Image and video generation are optional and may incur costs. For English narration, use a verified, user-approved English-capable voice or supplied audio rather than assuming that the legacy preset supports English.

## Choose the delivery scope

- **Prompts only:** Read [prompt-workflow.md](references/prompt-workflow.md) and deliver self-contained prompts without paid calls.
- **Sample:** Produce the requested segment, or a representative 10–15-second shot to verify characters, strokes, subtitles, and pacing.
- **Complete video:** Read [installation and preflight](references/preflight-and-recovery.md) and [production workflow](references/automation-workflow.md). Validate a representative shot before continuing; pause only when the user requests approval or a consequential decision is necessary.
- **Revision:** Preserve audio, timelines, and assets that do not require changes; redo only affected stages.

## Choose one of two production routes

| Desired result | Production route | Required reading |
|---|---|---|
| Drawing while narrating, visible strokes, a pen following the lines | Stroke-by-stroke storytelling | [stroke-story-workflow.md](references/stroke-story-workflow.md) |
| Process cards, relationships, independent elements, deterministic text | Programmatic animation | HyperFrames + SVG/HTML + GSAP; [automation-workflow.md](references/automation-workflow.md) |

After choosing stroke-by-stroke storytelling, select composition and visual style independently:

- **Composition:** Single scene, continuous multi-scene story, or left-to-right dual semantic islands that retain earlier content. Dual semantic islands are a composition technique within stroke storytelling, not a separate production route. See [semantic-island-storytelling.md](references/semantic-island-storytelling.md).
- **Visual style:** Natural-skin-tone chibi characters, Xiaohei style, or another requested hand-drawn style. Chibi characters suit biography and history; Xiaohei suits abstract arguments, methods, and metaphors. Either style can use any composition.

Scene-video generation and Flow/Nano Banana prompt-only delivery are optional delivery methods, not a third route. For continuous natural character motion or complex camera movements, first verify model availability, costs, and consistency limitations. For prompts only, read [prompt-workflow.md](references/prompt-workflow.md).

Stroke storytelling uses the bundled MIT backend in `vendor/srt-whiteboard-animation/`. It contains no second `SKILL.md` and does not trigger independently or request redundant approvals. The main skill coordinates routing, narration, subtitles, rendering, and verification. If the runtime is unavailable, preserve completed assets and report the gap. Never pass off SVG animation as genuine stroke-by-stroke drawing without explicit user approval of the alternative.

## Optional visual styles

- **Chibi character stories:** Natural skin tones and clear anatomy, age, and clothing anchors; suitable for biographies, history, and personal perspectives. See [q-human-story-style.md](references/q-human-story-style.md) and the [Steve Jobs example](examples/stroke-story/steve-jobs/README.md).
- **Xiaohei style:** Pure white, sparse black lines, restrained red/orange/blue, negative space, and deadpan visual humor; suitable for methods, systems, states, and metaphors. Read [visual DNA, attribution, and prompt framework](references/xiaohei-style.md) before using this built-in preset. Retain the Xiaohei name to credit Ian's open-source project.

Programmatic knowledge graphics are a production route, not a visual style. See the [What Is a Skill? demo](examples/program-animation/skill-demo/README.md). Stroke-story examples: [Three Articles of Law](examples/stroke-story/yuefa-sanzhang/README.md) and [The Life of Steve Jobs](examples/stroke-story/steve-jobs/README.md).

Reference images apply only to the current project unless the user requests a new saved preset. Record character, visual style, motion, and voice independently; a change in art direction does not require new narration.

## Public defaults and local configuration

[preferences.json](preferences.json) contains only non-secret defaults. User instructions and project `DESIGN.md` take precedence. The legacy finished-video preset uses Volcengine `seed-tts-2.0`, speaker `zh_male_liufei_uranus_bigtts`. Other authorized voices may be selected explicitly; reuse qualified audio matching the script first. Do not silently substitute system speech, edge-tts, or other low-quality local TTS. If an authorized, language-appropriate audio track is unavailable, continue independent prompt, visual, and silent production stages and report narration as incomplete.

Read [installation](docs/INSTALL.md) and [configuration](docs/CONFIGURATION.md) on first use, then run:

```text
python scripts/setup_check.py
```

Before first narration or a long render, run the route-specific preflight. A failed preflight blocks only dependent stages; do not redo approved audio, illustrations, or subtitles.

## Core production rules

1. **Preserve content:** Save original script, synthesis script, and subtitles separately. Do not remove claims, numbers, or qualifiers without permission.
2. **Audio first:** Reuse a complete matching track where possible; synthesize new narration as a whole or in natural sections.
3. **Time from real audio:** Use valid timestamps, forced alignment, or reviewed sentence-level pauses; never describe estimated timing as word-level alignment.
4. **Animation explains:** Reveal ink in semantic regions for stroke stories; use controllable elements for programmatic animation. Whole-image pans, zooms, and fades are supplementary only.
5. **Control drawability:** True stroke speed depends on region duration and source complexity. `hand-follow` smooths the displayed hand only; it does not slow the actual strokes.
6. **Deterministic text:** Render dates, proper names, logos, long text, and critical figures using subtitles or deterministic text layers, not image-model guesses.
7. **Validate a representative shot:** Check character consistency, pen lifts, color fill, occlusion, keywords, and subtitles before batch rendering.
8. **Validate real output:** Fully decode the MP4 and inspect every scene, semantic boundary, cut, audio track, and final 0.3–0.5 seconds.

## Safety, costs, and accuracy

- Never commit API keys, tokens, cookies, request headers, private absolute paths, or private model directories to the repository, commands, reports, or project ZIPs.
- Account-based narration, image, and video generation may cost money. Reuse matching caches and avoid blindly retrying requests with unknown outcomes.
- Verify real people, companies, logos, dates, and numbers using reliable sources or deterministic assets. Style references do not guarantee factual accuracy.
- For a complete video, deliver at least a real MP4; where supported, retain SRT, narration, timeline, source images, annotations, and editable projects.

See [quality-and-delivery.md](references/quality-and-delivery.md) and the [README](README.md).
