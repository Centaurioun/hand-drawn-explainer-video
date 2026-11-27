# Configuration

The public repository retains the Liu Fei voice ID as the upstream preset, without credentials or private absolute paths. Copy config/runtime.example.json into the project and customize it. Project DESIGN.md and current user instructions take priority.

## Narration

Prefer a qualified matching existing track, then an authorized voice. The legacy Volcengine preset is `zh_male_liufei_uranus_bigtts`; for English select a verified language-compatible voice. System speech and edge-tts are not default finished-video alternatives. The Volcengine helper reads credentials from environment variables:

```powershell
$env:VOLCENGINE_TTS_API_KEY = 'SET_IN_CURRENT_TERMINAL_ONLY'
pwsh -File scripts/volcengine_tts.ps1 -TextFile project/narration.txt -OutputFile project/assets/narration.mp3 -DryRun
```

Remove -DryRun only after verifying the request. Add -Speaker '<authorized-speaker-id>' when an alternative voice is explicitly selected. Verify current endpoint, resource ID, and speaker availability with the provider. Never commit keys to .env.example, screenshots, logs, or issues.

## Visuals

Defaults: 1920×1080 at 30 fps. For portrait or square video, update source images, annotation canvas, subtitle safe areas, and final manifest together. Tune hand size independently of hand-follow, which smooths hand motion without changing stroke speed.

## Cost and caching

Before cloud calls, identify provider, model, estimated request count, and cache strategy. If a connection drops with an unknown result, inspect outputs and provider records before retrying. Audio cache entries must match the script digest, voice, model, and file digest.
