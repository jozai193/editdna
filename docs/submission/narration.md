# Demo narration

The revised walkthrough uses Deepgram Aura-2 Asteria (`aura-2-asteria-en`), the model configured in the local Jarvis content-video setup. The narration is synthesized, not a human recording. The original sample tutorial's audio remains intact in the closing rendered-output excerpt.

The scene script and screenshots remain the same. Scene durations follow the new narration. Narration is normalized to a target of -16 LUFS, with a -1.5 dB true-peak target. This production step does not add a runtime API dependency to EditDNA.

Generate the revised version using an environment-provided `DEEPGRAM_API_KEY`:

```powershell
$env:EDITDNA_DEMO_TTS='deepgram'
$env:EDITDNA_DEMO_VOICE='aura-2-asteria-en'
.\.venv311\Scripts\python.exe scripts/create_walkthrough.py
```

Output: `docs/submission/editdna-demo-deepgram.mp4`. The generator caches completed narration locally and does not store credentials. Deepgram receives only the public narration script for synthesis. Jarvis code and runtime configuration are unchanged.
