# Installation

## Lightweight installation

Place this repository in the Codex skills directory and name the folder `hand-drawn-explainer-video-nikola`. Prompt-only mode needs no media dependencies. Scripts require Python 3.10 or later. On Windows with multiple Python versions, use `py -3.12` or a confirmed interpreter path.

```powershell
git clone --branch localization/english-only https://github.com/Centaurioun/hand-drawn-explainer-video.git "$env:USERPROFILE/.codex/skills/hand-drawn-explainer-video-nikola"
python "$env:USERPROFILE/.codex/skills/hand-drawn-explainer-video-nikola/scripts/setup_check.py"
```

The check should show at least `skill_files.ok: true` and `capabilities.prompt_only: true`. A folder containing only .git, a truncated ZIP, or a missing root SKILL.md indicates an incomplete download; rename or remove the incomplete copy and clone again. A false capability indicates missing configuration for that feature, not failure of prompt-only mode.

Alternatively clone elsewhere and run `scripts/install.ps1`. It does not overwrite existing directories.

## Stroke-story rendering

The backend is bundled; no separate srt-whiteboard-animation skill is required. First run:

```powershell
python vendor/srt-whiteboard-animation/scripts/prepare_env.py
python scripts/stroke_story_preflight.py --report preflight-stroke-story.json
```

The setup creates an isolated .venv in the backend directory without modifying system Python. If corporate networking blocks package repositories, create a virtual environment manually, install requirements-media.txt, and pass its interpreter to preflight with --backend-python.

The core stroke renderer requires no Informative Drawings, Anime2Sketch, PyTorch, neural weights, or GPU. It uses region masks, OpenCV processing, and skeleton path tracing. Only generating new illustrations from scripts may require external image services.

## Full MP4 and programmatic animation

- Final composition requires working FFmpeg and FFprobe on PATH.
- Programmatic animation requires Node.js 20+, Chromium/Chrome/Edge, and HyperFrames. npm installs GSAP; distribution files are not bundled.
- Cloud narration and image/video generation are optional and may incur fees. Users may supply narration and source art directly.

Initial Python/npm/HyperFrames installation requires access to their package sources. Fix proxy, certificates, and mirror configuration before treating failed downloads as missing skill files. Install FFmpeg from [the official download page](https://ffmpeg.org/download.html) or a trusted package manager, then rerun setup_check.py. Do not use incomplete private editor builds.

The upstream voice preset is Volcengine Liu Fei (`zh_male_liufei_uranus_bigtts`). Verify voice/language compatibility and authorization for English narration or use supplied audio. Without suitable narration, prompts, storyboards, and some visual stages remain possible. Never silently substitute system speech or edge-tts.

## OpenAI skill upload

The Skills API accepts a directory or single ZIP. SKILL.md must be at the ZIP root, not nested under an extra directory. See [official Skills documentation](https://developers.openai.com/api/reference/python/resources/skills/methods/create).

Restart or refresh the skills-enabled client and test a README prompt.

## New environment acceptance

1. Run scripts/setup_check.py and resolve route-specific dependencies.
2. Prompt-only work does not need media packages.
3. For stroke videos, prepare the isolated environment and run stroke_story_preflight.py; it must generate and decode a small real MP4.
4. For programmatic animation, verify Node.js, browser, FFmpeg/FFprobe, then run npm install and npm run check in the example.
5. Before paid narration, dry-run the authorized language-appropriate voice; do not make unauthorized calls or silently fall back.
6. Declare completion only after fully decoding the real MP4 and checking audio, subtitles, scenes, and final frames.
