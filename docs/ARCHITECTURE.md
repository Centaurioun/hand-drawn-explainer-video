# Architecture

```text
User content / SRT / reference images
                  ↓
Single skill routing and script design
         ┌────────┴──────────┐
Stroke storytelling       Programmatic animation
Bundled MIT backend       HTML/SVG/HyperFrames
         └────────┬──────────┘
Narration + timeline + deterministic subtitles/keywords
                  ↓
Final MP4 + editable assets + validation report
```

`vendor/srt-whiteboard-animation/` is a runtime library, not a second skill. It contains no `SKILL.md`, agent metadata, or independent trigger rules. This preserves continuous-stroke capabilities without conflicting with the main skill. See its `UPSTREAM.md` and MIT `LICENSE` for origin and modification boundaries.

Style, audio, and rendering are independent layers. Changing the art style must not automatically change the voice; rebuilding a scene must not regenerate approved narration.
