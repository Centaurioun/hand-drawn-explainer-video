# Troubleshooting

## Stroke preflight cannot find Python

Run `python vendor/srt-whiteboard-animation/scripts/prepare_env.py`. For a custom environment, pass its interpreter to `scripts/stroke_story_preflight.py --backend-python <path>`.

If pip reports proxy, certificate, or version errors, verify Python 3.10+ and check proxy/mirror configuration. You can prepare an environment with requirements-media.txt on a connected system. Never commit .venv.

Repeated ProxyError messages followed by No matching distribution found usually indicate unreachable package sources; do not arbitrarily downgrade dependencies. Fix networking or use a trusted mirror, then rerun preparation. The existing virtual environment can be reused to install missing dependencies.

## The hand moves too fast

Lowering hand-follow smooths hand motion but does not slow ink. Increase region duration, split semantic regions, or simplify the source art. Ensure main contours, color fill, and at least 0.5 seconds of finished-image hold remain readable.

## Later regions appear prematurely

Check bounding boxes, cross-island connected lines, and protectedRegions. Keep a 6–10% gutter between islands; do not let background lines cross it.

## Missing color or sudden zoom in the last frame

Compare the last 0.3–0.5 seconds with the approved image. Enable source-image fading only if missing color is confirmed; normally use --source-overlay never.

## GSAP is missing

Run npm install in the demo project. predev, precheck, and prerender copy the browser file from npm into assets/. Never commit an unverified minified script.

## HyperFrames cannot find or run FFmpeg

setup_check.py considers only working FFmpeg/FFprobe discoverable from the command line. If a valid build is not on PATH, configure its absolute path locally or use HyperFrames' temporary HYPERFRAMES_FFMPEG_PATH and HYPERFRAMES_FFPROBE_PATH environment variables. Do not permanently change system PATH for one project.

Finding a file does not prove its encoder works. Windows STATUS_DLL_NOT_FOUND usually means missing companion DLLs; minimal builds may also lack WAV decoding or AAC encoding. Use a complete standalone 64-bit build and verify its version and short audio/video tests before rendering.

## Images exist but the video cannot be completed

Save source images, narration, SRT, timeline, and annotations; identify missing FFmpeg, browser, account, or model capability. Do not claim static images or SVG fades are completed stroke-story videos.
