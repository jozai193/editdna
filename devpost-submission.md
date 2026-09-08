# Title
EditDNA

## One-line Summary
Your finished edits become instructions: learn recurring cuts and framing, then apply them to the next recording with evidence you can inspect.

## Problem
Creators repeat small editing decisions on every recording: shorten pauses, choose between repeated takes, and crop consistently. A generic preset cannot learn which of these decisions a particular creator actually makes. Explaining those preferences repeatedly also makes delegation expensive.

## Solution
EditDNA learns a small, transparent editing profile from a creator's own raw-to-final examples. It finds where finished speech came from, lets the creator review that correspondence, and measures recurring preferences across independent recording sessions. A new recording becomes a reviewable edit plan with real MP4 output, captions, and a provenance manifest.

## Why This Matters
The intended benefit is a faster first pass through routine editing while retaining creator control. The prototype automates pause trimming, conservative equivalent-take selection, and fixed centered framing. A local timed pilot measures manual and assisted editing under the same quality target; no human time-saving result is claimed before both tasks are completed.

## How We Used AI
Local Whisper speech recognition provides word timestamps. Waveform correlation aligns raw and finished audio. Small-data statistics learn pause spacing and repeated-take preference from reviewed examples. Corresponding visual frames support a bounded centered-crop estimate; three independent sources are required before that framing becomes a learned preference. This does not fine-tune a foundation model or infer a creator's entire aesthetic.

## How We Used Codex
Codex helped translate the architecture into the Python media engine, FastAPI service, SQLite state, and React editor; generated our owned demonstration corpus; implemented tests; and investigated concrete failures including video timing drift, zero-duration transcript tokens, undo state, and source-match inputs retaining values from another example. Codex also prepared the reproducible evaluation, local timing protocol, documentation, and browser checks.

## Key Features
- Import real video/audio and pair originals with finished edits.
- Inspect and accept audio correspondence and visual framing evidence.
- Learn immutable versions of pause, equivalent-take, and centered-framing preferences.
- Generate a personalized edit; compare it with a generic baseline.
- Restore cuts, change boundaries, lock segments, and undo revisions.
- Export an actual MP4, SRT/VTT captions, edit plan, and source-hash manifest.
- Run a server-timed manual/assisted editing pilot with a quality gate.

## Architecture
React/Vinext review interface → local FastAPI service → durable SQLite job queue → FFmpeg and local Whisper. Reviewed source correspondences become versioned preferences. Each export pins its source, profile, and plan revision. Native media processing runs locally; the hosted demo presents real previously generated artifacts.

## Testing Instructions
1. For a quick inspection, open the public demonstration, choose either creator profile, and compare its rendered output with the generic edit. Inspect example pairs and the evidence page.
2. For actual processing, clone the public repository. Install Python 3.11, Node.js 22.13+, FFmpeg, and ffprobe. Run `Setup-EditDNA.ps1`, then `Start-EditDNA.ps1` from the checkout.
3. Open the local app at http://localhost:3000. Its shipped examples work without a channel account or API key. Import your own footage to test the full workflow. First-time transcription downloads the speech model.
4. The test suite has 21 passing checks, including actual FFmpeg timing/decode, revision conflicts, undo of framing, independent-session requirements, and timing-result gates. Authored app lint, TypeScript, and production build pass.

The constructed corpus contains five original slide tutorials with synthesized narration. Three sessions train the profiles; two different sessions evaluate transfer. The regression run recovered 50/50 accepted audio correspondences within 100 ms, matched all 16 take decisions, and achieved a 5 ms pause-target error versus 235–265 ms for the generic preset. Both demonstrated framing preferences (1.00× and 1.10×) transferred with zero estimated zoom error. These tutorials were used during integration debugging, so this is not a sealed benchmark.

## Public Demo Link
Publication in progress; insert the verified URL before submitting.

## Public Repository Link
Publication in progress; intended repository: https://github.com/jozai193/editdna

## Demo Video
`docs/submission/editdna-demo.mp4` — narrated walkthrough using actual application captures and an actual rendered output. Synthesized narration is disclosed. Add a public video link when uploaded.

## Screenshot Shot List
- `docs/submission/studio.png`: review workspace and learned framing.
- `docs/submission/examples.png`: raw-to-final examples.
- `docs/submission/profile.png`: learned preference and evidence.
- `docs/submission/evaluation.png`: measured regression results and limits.
- `docs/submission/timed-trial.png`: human timing protocol before starting.

## Submission Readiness Notes
Official requirements rechecked through Devpost on September 8, 2026: working creator automation, built during the event; video and hosted website are optional. Deadline: September 8 at 12:00 UTC / 17:30 IST. The account is registered. This file is a draft; EditDNA has not been submitted by this workflow. Keep it separate from the existing RetentionDNA entry.

## Known Limitations
Best suited to clear English speech and mostly unchanged source audio. Music, denoising, dubbing, speed changes, and inserted footage can defeat alignment. Equivalent-take selection depends on accurate transcripts. Visual learning covers a fixed centered crop only; review faces and edge text. It does not learn grading, graphics, narrative order, or crop timing. The local edition uses one worker. The public demo cannot process uploads. No real-channel, retention, or population-wide creator time-saving result is claimed.

## TODO Official Form Fields
No custom fields were returned by the official requirements tool. Review the actual project form before final submission. Use the concrete demo and source links once verified; add human timing evidence only after completion.
