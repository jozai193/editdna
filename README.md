# EditDNA

EditDNA learns recurring editing decisions from your own raw-to-final examples, then applies those preferences to a new recording. Every inferred match and every resulting cut is reviewable.

The working local application supports video/audio import, waveform alignment, local transcription, learned pause spacing, conservative repeated-take selection, learned centered framing, a timed human editing trial, immutable profile versions, cut editing, locks, undo, and real MP4/caption/JSON exports. It does not require a YouTube account or a paid API key.

## Run on Windows

Requirements: Python 3.11, Node.js 22.13 or newer, FFmpeg and ffprobe on PATH. Install dependencies once:

```powershell
Set-Location 'E:\content engine hackathon'
.\Setup-EditDNA.ps1
.\Start-EditDNA.ps1
```

Open **http://localhost:3000**. Stop the processes created by the launcher with `./Stop-EditDNA.ps1`. Original recordings and the SQLite database live in the ignored `data/` folder. The launcher has no automatic startup registration.

The API listens only on `127.0.0.1:8765`. Interactive API documentation: http://127.0.0.1:8765/docs. Run a single API instance; its background worker processes one job at a time. The local UI uses the Sites/Vinext development server. The production web build is a separate, read-only demonstration of actual generated outputs.

If the first dependency installation fails behind a managed proxy, use a pip version with system certificate support. Do not disable certificate validation. On this machine installation succeeded with `python -m pip --python .venv311 install -r requirements-lock.txt`.

## Use your recordings

1. Import your raw recording and its finished edit. Audio is required. Maximum duration is 20 minutes and maximum upload size is 2 GB.
2. Create a creator profile, then add the raw/final pair in **Example library**.
3. Analyze the pair. Play each candidate source match, choose an alternative or adjust its source timestamp if needed, and accept reliable matches.
4. Transcribe the raw recording locally if you want take preferences. The first transcription downloads the `base.en` Whisper model; later runs use the local cache. The default is CPU int8. Set `EDITDNA_ASR_MODEL` to a compatible model name or local path before starting the API to change it.
5. Analyze corresponding visual frames, inspect the source/final frames, and accept reliable crop estimates. Three independent sources are needed for a learned fixed centered crop. Learn a profile from accepted examples. Three independent raw recordings are required before a repeated-take preference can be applied. Pause estimates from fewer sessions are blended with the default and labeled limited.
6. Import another recording, transcribe it, select a profile version, and create an edit. Compare the generic baseline, restore omitted takes, adjust boundaries, remove or lock segments, and undo changes.
7. Render the reviewed revision. Download the MP4 or the ZIP containing MP4, SRT, VTT, edit-plan JSON, and a provenance/hash manifest. Captions contain words only when transcription has been generated.

Transcribe before creating a plan: existing plans are immutable snapshots and do not silently acquire new transcript text or new profile preferences.

## Architecture

```text
Media upload → validated original + audio features
Raw/final audio → normalized waveform correspondence → accepted matches
Accepted matches + source transcript → versioned preference profile
New source + pinned profile → constrained edit plan → review/revision
Pinned revision → FFmpeg renderer → MP4 + captions + reproducibility manifest
```

- `engine/media.py`: media validation, extraction, speech regions, timestamp-based rendering.
- `engine/learning.py`: alignment, pause statistics, exact-transcript duplicate groups, take evidence, edit planning.
- `service/store.py`: SQLite WAL records, atomic revision checks, kind-scoped identifiers.
- `service/main.py`: FastAPI endpoints, persistent job queue, single background worker, export bundles.
- `web/app/page.tsx`: working React editor and read-only hosted demo.
- `web/lib/contracts.ts`: frontend data contracts.
- `scripts/`: demonstration generation, evaluation, and packaging.
- `docs/hackathon-build/spec.md`: original architecture proposal. `implementation-status.md` distinguishes implemented features from the broader plan.

The learning code receives extracted media features and accepted correspondences. It does not read demonstration recipes, filenames, or hidden reference edit maps. No foundation model is fine-tuned. The learned rules are transparent, small-data statistics.

## Demonstration and evaluation

Five original tutorial sessions use original slides and Windows synthesized speech. Each has two independently rendered constructed editing styles. Sessions 1–3 provide training examples; sessions 4–5 are excluded from learning. Their outputs were inspected during integration debugging, so the reported results are regression measurements, not an untouched final benchmark.

```powershell
.\.venv311\Scripts\python scripts/create_demo.py
.\.venv311\Scripts\python scripts/add_visual_examples.py
.\.venv311\Scripts\python scripts/transcribe_demo.py
.\.venv311\Scripts\python scripts/evaluate.py
.\.venv311\Scripts\python scripts/package_demo.py
```

`data/demo/evaluation.json` records the measurements. Reference edit maps stay in `data/demo/ground-truth.json`; the evaluator alone uses them. `package_demo.py` copies real outputs into `web/public/demo/` and archives superseded generated records from the local view without deleting the source artifacts.

For this constructed corpus, the verified run matched 50 accepted audio correspondences within 100 ms, learned pause targets of 0.11 and 0.61 seconds, and agreed with all 16 tested take decisions across the two held-out sessions. Pause-target error was 5 ms versus 235–265 ms for the fixed generic baseline. These measurements are not evidence of creator time savings, audience retention, or general editing quality.

## Checks

```powershell
New-Item -ItemType Directory -Path data/test-runs -Force | Out-Null
$testRun = Join-Path (Get-Location) ('data/test-runs/' + [guid]::NewGuid().ToString('N'))
.\.venv311\Scripts\python -m pytest -q --basetemp $testRun
Set-Location web
npm run lint
npx tsc --noEmit
npm run build
```

Application lint covers authored `app/` and `lib/` source. The generated component catalog has separate upstream lint findings and is not modified merely to satisfy this project's lint rules.

## Current limits

- Best suited to clear, English, single-speaker material and mostly unchanged source audio. Music, heavy denoising, speed changes, dubbing, and B-roll can make audio alignment unreliable.
- Exact transcript equality is conservative but transcription can still be wrong. Review equivalent-take decisions. Different numbers and negations are retained when represented correctly in the transcript.
- The speech detector is an amplitude heuristic. Quiet speech, long internal pauses, and unusual microphone conditions need manual review.
- Visual learning currently covers fixed centered framing only (1.00–1.40×), with abstention on ambiguous matches. B-roll selection, narrative rearrangement, emotion, custom typography, and learned graphics are not implemented.
- Jobs persist across restart, but this edition uses one process rather than distributed leases. Only queued jobs can be cancelled. Do not run multiple API workers against the same database.
- The hosted demo cannot process uploads. Native FFmpeg and speech inference run locally; they are not simulated in the hosted interface.
- No creator study, real-channel test, hackathon submission, or claim of likely winning is included.

Code: MIT. Third-party packages, FFmpeg, speech models, and operating-system voices retain their respective licenses.

## Release status

The application tests and HTTP upload/edit/export checks pass locally. The web dependency audit reports zero known vulnerabilities after patching the starter dependencies. Browser checks cover the editor, rendered playback, visual evidence, and trial preparation. 21 automated tests pass.

Hosted publication is being prepared; the public release notes record the verified URL once deployed.

## Human timing pilot

Open `/trial` in the local app. The clock starts only when you start a task and includes edits, render wait, and playback review. Finish both conditions to download the recorded evidence. This is a one-participant controlled pilot on constructed tutorials; training and transcription are excluded, and prior exposure, task length, and task order can affect the result. No creator time-saving percentage is claimed before an actual human completes both tasks.
