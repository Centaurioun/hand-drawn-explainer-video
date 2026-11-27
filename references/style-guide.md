> Scope: This file covers image-generation and Flow prompt-only mode. For programmatic animation, follow SKILL.md, DESIGN.md, and the approved sample; do not impose the no-label-card or static-keyword rules below.

# Q Doodle Crayon Style and Motion Reference

This optional written style specification has no bundled example image or verified animation project. Apply its palette, strokes, and motion only when selected. Adapt conflicting constraints to new user references. See [style selection and updates](style-selection-and-updates.md).

## Visual signature

Repeat these core constraints in each image prompt to reduce drift:

```text
modern Q-version hand-drawn crayon illustration, vertical 9:16, solid warm-white canvas background, exact base color #F8F6EF, only extremely subtle low-contrast paper grain, thick imperfect black hand-drawn marker/crayon outlines, bold flat wax-crayon blocks, sunflower yellow, saturated cobalt blue and vivid tomato red with only a small muted-green accent, natural restrained Q-version proportions, simple hand-drawn composition, 2–4 large readable visual groups, generous breathing room, no glossy rendering, no realistic lighting, no logos, no watermark, no photorealism, no 3D
```

## Fixed background color

Use the same background constraints for all stills and final frames:

```text
Use a flat, uniform warm-white canvas background with exact base color #F8F6EF. Preserve the same background color across every shot. Add only extremely subtle low-contrast paper grain. No black background, no gray-brown tint, no yellow-beige color cast, no gradient, no vignette, no colored paper, no border shadow.
```

Natural-language Flow prompts cannot guarantee exact pixel colors. Use a fixed `#F8F6EF` First Frame or normalize the background afterward if exact matching is necessary.

## Keyword mode

For on-screen keywords, choose short phrases and specify exact wording, placement, and safe zone:

```text
Show the exact English keyword “Curiosity” as small, clean, high-contrast hand-drawn lettering directly on the warm-white illustration paper near the upper-left margin, not inside a card, label, sticker, note or text box. Keep it perfectly legible and unchanged throughout the shot, and do not add any other text.
```

Write directly on the paper, in negative space, or beside relevant objects. Avoid sticky notes, label cards, stickers, rounded text boxes, title panels, standalone white cards, and bottom caption boxes. Keep text out of subtitle areas, faces, fast-moving objects, and complex backgrounds. Text should occupy no more than 10–12% of frame height and remain still, legible, and undistorted. Flow may misspell even short words; provide a text-free alternative for names, amounts, dates, and long sentences.

Slightly oversized heads and smaller bodies are acceptable, but avoid extreme proportions, bulging eyes, or childish cartoon styling. Use hairstyle, glasses, clothing, posture, and props as identity anchors rather than photorealism. Exaggerate objects and their relationships for humor. Keep backgrounds clean: no complex rooms, cyber HUDs, vintage newspapers, yellowed paper, muted brown-gray casts, dense crosshatching, or pseudo-writing.

## Composition rules

- Use 9:16 portrait format; the central group usually occupies 60–70% of width. Reserve top and side keyword space and a clear lower subtitle zone.
- Use 2–4 major visual groups, readable within a second on mobile. Avoid tall stacks, tiny characters, intricate machinery, and poster-like clutter.
- Specify left/center/right, foreground/background, and vertical relationships instead of abstract emotion alone.
- Render real logos, company/person names, dates, amounts, and long sentences in post-production. Short keywords may be handwritten on paper or near objects. Text-free variants retain clean negative space without text containers.

## Real-entity anchors

Use these rules when depicting real entities:

```text
For an exact national flag, preserve the official country name, flag colors, geometry, emblem placement and aspect ratio. Do not substitute a similar flag, random flag or abstract color pattern.
For a real company, use its industry, products, hardware and restrained brand-color cues. Do not invent or deform the exact logo unless an approved reference image is supplied.
For a famous person, use a clearly stylized non-photorealistic chibi caricature with public identity cues such as hairstyle, glasses, clothing and posture. Do not bypass safety restrictions or attempt a photorealistic face clone.
```

When a flag or logo is essential, recommend a reference image or original overlay; the model supplies surrounding chibi composition and action. More descriptive adjectives do not guarantee entity accuracy.

## Flow image-to-video motion syntax

Structure prompts in this order:

1. `Start from the supplied completely blank #F8F6EF warm-white paper frame.`
2. Keep a `locked flat frontal camera`; slide in base objects or reveal them with irregular crayon lines.
3. Introduce characters and secondary objects as `rigid flat paper cutouts` with slight settling bounce.
4. Reveal relationships last: magnifier over meter, weight on cloud, coins approaching mouth, or hand pressing switch.
5. For the last 0.8 seconds, `settle into and hold the exact supplied final illustration`.

Specify `tactile 10–12 fps paper stop-motion`, no camera movement/zoom/parallax, liquid morphing, lip sync, additional characters/logos, watermarks, or audio. If keywords are enabled, keep them on paper or beside objects, static, legible, undistorted, without extra text or containers.

For Flow First + Last, First Frame is blank warm-white paper and Last Frame is the numbered completed still. Explicitly identify final composition and style reference. If only the completed image is available, use:

```text
Animate the supplied completed illustration in place for about 5 seconds while preserving every drawn shape and the exact composition. Use only restrained paper-cutout micro-motion: one or two small object bounces, a short hinge-like hand movement, subtle wheel rotation or one accent appearing. End on the unchanged supplied illustration and hold it still for the final second.
```

## Visual metaphor reference

| Narration relationship | Preferred metaphor |
|---|---|
| Competition / losing a race | Race, chase, tug-of-war |
| Cost / consumption | Leaks, weights, money-eating monster, meter |
| Verification / earnings | Exam, touchstone, health check, magnifier |
| Choice / conclusion | Fork, balance, switch, two doors |
| Risk / pressure | Crack, alarm, unstable blocks, countdown |
