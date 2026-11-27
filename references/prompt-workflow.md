# Original Prompt-Only Workflow

Use only when the user requests prompts or explicitly chooses external generation through Flow/Nano Banana. Do not call APIs, buy credits, or render video.

If no other style is specified, read [style-guide.md](style-guide.md) for the Q Doodle crayon style and Flow first/last-frame syntax. For reference images, follow [style-selection-and-updates.md](style-selection-and-updates.md), replacing conflicting colors, strokes, proportions, and backgrounds. The crayon example is not a universal style rule. [output-example.md](output-example.md) illustrates format, not a factual source for new projects.

Split by meaning, often into 4–6-second shots, subject to script and user requirements. Each shot has one core visual metaphor and self-contained prompts; never write "same as above."

```text
Shot 01
Narration:
Suggested duration:
Visual metaphor:
On-screen keywords:

[Image generation prompt]
Complete English description: 9:16, #F8F6EF, restrained chibi characters,
thick black hand-drawn lines, yellow/blue/red palette, precise placement,
subject area and subtitle safe zone.

[Image-to-video prompt]
Use the finished illustration as Last Frame and blank warm-white paper
as First Frame. Locked camera, rigid paper cutouts, tactile paper stop-motion.
Specify appearance order, character actions, and exact final frame.
No lip sync, added characters/logos, or audio.

[Entity accuracy]
Specify text, flags, logos, dates, and figures requiring original assets
or deterministic post-production layers.
```

For a single reference image, request restrained in-place motion rather than nonexistent first-frame controls. Do not guarantee pixel-perfect backgrounds, text, or flags. Provide a text-free fallback for generated short keywords; render long text and precise numbers in post-production.

Do not introduce narration configuration, project packaging, or sample approval for prompt-only requests.
