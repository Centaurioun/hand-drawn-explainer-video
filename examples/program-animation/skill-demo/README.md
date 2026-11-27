# What Is a Skill? Programmatic Animation Example

A 36-second editable HTML/SVG/HyperFrames project with eight scenes, original narration, timeline, and deterministic text. It demonstrates independent process and relationship animations, not stroke storytelling.

![Original programmatic-animation cover](preview.png)

[Watch the original 14-second MP4](what-is-skill-sample.mp4). Characters, bubbles, nodes, arrows, and text are independent SVG/HTML elements driven by GSAP/HyperFrames using narration timing.

The editable HTML, script, and captions have been translated into English. The bundled WAV, MP4, and PNG are unchanged upstream Mandarin-language demonstration assets. English captions follow the original scene timings; they are not a newly synthesized or verified English audio track. Replace narration and realign timing for an English-spoken export.

```powershell
npm install
npm run check
npm run dev
npm run render
```

npm installs pinned GSAP; lifecycle scripts copy the browser bundle to assets/gsap.min.js. Generated files are not committed and GSAP's license applies. HyperFrames is invoked at a pinned version.

For new projects prefer qualified user-supplied audio or an authorized language-compatible voice. Do not use sample audio or system speech as generic finished narration.
