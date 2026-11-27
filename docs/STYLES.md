# Production Routes, Composition, and Visual Styles

Keep these three concepts distinct:

```text
Production routes
├─ Stroke storytelling
│  ├─ Composition: single scene / multi-scene story / dual semantic islands
│  └─ Style: chibi characters / Xiaohei / other hand-drawn styles
└─ Programmatic animation
   ├─ HTML / SVG / GSAP
   └─ Process cards / relationships / exact text / knowledge graphics
```

| Type | Option | Suitable content | Example request |
|---|---|---|---|
| Visual style | Natural-skin-tone chibi characters | Biography, history, entrepreneurship | Draw the person's life stroke by stroke, with natural skin tones and changes in age. |
| Visual style | Xiaohei | Methods, abstract systems, deadpan metaphors | Draw in Xiaohei style on white with restrained colored annotations. |
| Composition | Dual semantic islands | Cause/effect, question/answer, before/after | Draw the left side first, then the right, preserving the left. |
| Route | Programmatic animation | Processes, rules, relationships, exact labels | Use HTML/SVG/GSAP for hand-drawn process cards with deterministic text. |

Dual semantic islands specify narrative and drawing order, not a third route or separate art style. Both chibi and Xiaohei can use any composition.

Hand-drawn aesthetics alone do not establish stroke animation. Requests for each stroke, pen following, or drawing while narrating call for the stroke route; independent cards, arrows, precise labels, and transformations call for programmatic animation.

The upstream commercial-skills video used independent SVG/HTML characters, cards, arrows, and text driven by GSAP/HyperFrames. Its hand-drawn look comes from styling and outlines rather than persistent raster ink. Stroke stories extract line art, trace skeleton/stream paths within semantic regions, and progressively fill color. The two routes can share narration, subtitles, and QA but must not be misrepresented.

See [Chibi characters](../references/q-human-story-style.md), [Xiaohei](../references/xiaohei-style.md), [Dual semantic islands](../references/semantic-island-storytelling.md), [Three Articles of Law](../examples/stroke-story/yuefa-sanzhang/README.md), [Steve Jobs](../examples/stroke-story/steve-jobs/README.md), and [What Is a Skill?](../examples/program-animation/skill-demo/README.md).
