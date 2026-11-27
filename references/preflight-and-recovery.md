# Runtime Preflight and Recovery

Read before first narration or long rendering. For text/color-only revisions with unchanged environment, reuse prior checks. Prompt-only mode requires no preflight.

## Select environments based on execution

Do not infer readiness from default python, package discovery, or existing directories. Use a verified isolated environment; retest after upgrades, model-path changes, or cleanup. Keep machine paths in local configuration (Windows: %LOCALAPPDATA%/CodexVideo/runtime.json), not distributed skills or ZIPs.

scripts/preflight.py performs local checks only, without credentials, narration calls, or installations. Configuration fields: node, hyperframes_cli (absolute JS entry), chrome, ffmpeg, ffprobe, media_python; independent ASR additionally requires asr_python and asr_model (actual model snapshot directory). Discover paths on the current machine.

For stroke stories also run scripts/stroke_story_preflight.py. It verifies the bundled backend, isolated Python, skeleton/contour-wipe options, and renders and decodes a tiny offline MP4 in a temporary directory. No installations or paid calls. See [stroke workflow](stroke-story-workflow.md).

```text
python <skill>/scripts/preflight.py --config <local-runtime.json> --mode render --report <project>/preflight-render.json
python <skill>/scripts/preflight.py --config <local-runtime.json> --mode asr --audio <existing-local-audio> --report <project>/preflight-asr.json
```

Render checks encode three H.264 frames, probe output, and launch Chrome through CLI dependencies to capture a screenshot. ASR verifies nonempty weights, configuration, and vocabulary, then loads and infers in an isolated subprocess (first five seconds of supplied audio). Import success and empty caches do not establish readiness.

Upstream verified Python 3.12 with faster-whisper 1.2.1/CTranslate2 4.8.1; see scripts/asr-requirements-tested.txt. This is a reproducible combination, not a required upgrade. Use isolated environments; do not modify system PATH or unrelated projects. Test existing audio, not paid resynthesis.

## Current distribution checks

Prefer CLI check/inspect/snapshot. Some animation-map scripts depend on development package @hyperframes/producer, not necessarily distributed with CLI. CLI availability does not establish all scripts work.

For granular mapping of single-page inline SVG/HTML/GSAP projects:

```text
node <skill>/scripts/animation-map.mjs <project> --cli <hyperframes-cli-entry> --browser <chrome-executable> --width 1080 --height 1920 --frames 2 --out <project>/animation-map
```

This compatibility entry discovers Puppeteer through CLI dependencies, without hard-coded npm caches or separate development package installation. It does not simulate nested compositions/video synchronization and rejects such projects; use official CLI and real MP4 verification instead.

## Recovery by failure type

- DLL initialization/access violation: record interpreter/dependencies and mark combination unavailable. Switch to preflight-verified isolation; do not repeat unchanged attempts or infer a specific root cause from another environment's success.
- Missing model weights: do not load. Choose a complete model; verify size, storage, and network before downloads. Do not download gigabytes automatically for optional review.
- Missing development dependencies: use compatibility entry or public CLI; do not modify global plugins.
- Browser timeout: retain stage/logs, check whether progress continues, terminate stalled subprocess, then optionally test --no-browser-gpu on a short sample. Software rendering is not universally faster.
- UTF-8 decoded using a legacy system encoding: specify UTF-8 explicitly and set PYTHONUTF8=1 for subprocesses if needed; do not change system locale.
- Layout issues: fix visuals, preserve approved audio. Place persistent headings/badges in shared layers; distinguish deliberate transition overlaps from normal collisions.

Preflight failures block only dependent stages. Valid native timestamps remain usable; independent ASR is extra review. Disclose missing ASR instead of claiming word-level validation from silence analysis. Keep naturalness and pronunciation pending listening review when unavailable.

## Before and after long renders

Finalize static layout → representative scenes, longest captions, transitions → full project checks → long render. Test a 3–5-second sample with character motion, at least one transition, audio, and video. Do not request already approved style again.

Fully decode the real MP4, inspect every scene/transition and ending. Fixed tools, exit 0, and HTML checks are not final media acceptance. Record actual paths, versions, results, and successful stages; retest if environment changes.
