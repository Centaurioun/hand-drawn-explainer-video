# Narration and Audio Alignment

## Defaults and reuse

The upstream finished-video preset is Volcengine Liu Fei (`zh_male_liufei_uranus_bigtts`), resource `seed-tts-2.0`. Prefer a complete, qualified recording matching the script. For English, confirm an authorized English-capable voice or use supplied audio; do not assume the original speaker is compatible. Explicitly select alternative voices and never change voice merely because the visual style changed. Check existing assets before incurring charges.

System speech, edge-tts, and other low-quality local TTS are not silent substitutes for finished narration. If authorization or suitable audio is missing, complete independent work and report the narration gap. A low-cost draft voice may be used only on explicit request; label it as placeholder and preserve approved narration.

Short explainers usually sound more coherent synthesized as a whole. Split longer requests at natural semantic boundaries using the same voice and settings. The helper's 1,500-character limit is conservative, not a permanent provider limit.

## Safe narration helper

scripts/volcengine_tts.ps1 uses a fixed official endpoint, records input/voice/audio digests and integrity metadata, reuses matching output, refuses mismatched overwrites, rejects responses without a complete end marker, and never automatically retries chargeable requests.

```powershell
pwsh -File <skill>/scripts/volcengine_tts.ps1 -TextFile <project>/narration.txt -OutputFile <project>/assets/narration.mp3 -DryRun
pwsh -File <skill>/scripts/volcengine_tts.ps1 -TextFile <project>/narration.txt -OutputFile <project>/assets/narration.mp3
```

Use PowerShell 5.1 (UTF-8 BOM script) or 7. DryRun checks input and plan without reading credentials or making requests. Omitting -Speaker uses the legacy Liu Fei default; explicitly pass -Speaker <speaker-id> for an authorized language-compatible alternative. Live synthesis requires user authorization.

Prefer the authorized VOLCENGINE_TTS_API_KEY environment variable, otherwise the same Windows user's %LOCALAPPDATA%/CodexVoice/volcengine-key.dpapi. Never include keys in arguments, skill configuration, JSON, or ZIPs. Advise rotation if a key was exposed; do not revoke it without authorization.

The helper implements https://openspeech.bytedance.com/api/v3/tts/unidirectional, X-Api-Key, resource ID, and request UUID, validating the completion marker. Verify current provider documentation before first use or after protocol errors; do not guess parameters or incur charges just to test.

Cache matching requires original script digest, voice, model resource, sample parameters, and audio digest. Refuse mismatched overwrites. For old audio without metadata, manually verify script, voice, and completeness; never fabricate request records or regenerate unnecessarily.

## Alignment

Before independent ASR review, follow [preflight](preflight-and-recovery.md): verify nonempty model files, load in an isolated environment, and infer on a short sample. Validate provider word timestamps for nonemptiness, order, boundaries, and script correspondence. ASR failure is not a reason to resynthesize.

Priority: valid word/sentence timestamps → forced alignment against original script → sentence-level ASR review → measured pauses plus human/audio review. Empty words arrays mean no word timestamps. Silence detection identifies pauses, not what was spoken; use full-sentence subtitles rather than fabricated word timing.

Check proper names, numbers, ambiguous pronunciations, and the final sentence. Correct missing or mispronounced audio rather than hiding it with corrected captions. Record differences between displayed text (e.g., Skill) and synthesis pronunciation separately.

## Naturalness and mixing

Preserve context, punctuation, and stable speaking rate before tuning style. Avoid arbitrary emotion parameters or word-by-word synthesis. If needed, compare a short passage while retaining the approved voice.

Do not regenerate approved narration for visual revisions. Optional music and sound effects require clear sources and appropriate rights; mix below narration. Check silence, clipping, pops, duration, final truncation, and sentence-to-sentence loudness. Minor encoder padding is acceptable within frame-level tolerance, but must never omit content.
