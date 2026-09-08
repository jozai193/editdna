# EditDNA implementation status

The original architecture describes a larger product. This build implements a coherent local vertical slice plus a read-only hosted demonstration.

## Implemented

- Validated media upload, content hashes, durable originals, extracted mono audio, waveform peaks, speech regions.
- Raw/final waveform correlation, competing matches, explicit acceptance/rejection and source-boundary correction.
- Session-balanced pause estimates, support labels, evidence links, immutable profile versions.
- Local Whisper transcription; exact adjacent transcript grouping; first/last take preference learned only from consistent selections across at least three source sessions.
- Generic/personalized plans with the same speech-region candidates, unique-content preservation, source order, editable boundaries, restore/remove, segment locks, revision conflicts, undo.
- Persistent SQLite job records, sequential worker, restart recovery, queued cancellation and duplicate pending-job reuse.
- Source-timestamp video selection, sample-timed audio concatenation, bounded fades, MP4 encoding, caption remapping, export bundles and hashes.
- Four product views: editing workspace, example/alignment library, creator profiles, evaluation/exports.
- Five owned demonstration sessions, two constructed profiles, two sessions excluded from learning, real rendered outputs and transparent measured limitations.

## Architecture adaptations

SQLite records use a generic JSON-body table with a `(kind,id)` primary key rather than SQLAlchemy entity tables. The worker runs in the local API process with a single worker thread rather than a separately deployed lease-based service. The frontend uses the required Sites starter (React/Vinext) rather than a standalone Vite SPA. Hosted processing is not available: the hosted app presents the real local demonstration artifacts.

Take learning is a supported first/last preference for exact repeated transcripts, not a general logistic ranking model. Profile updates are explicit immutable versions. Feedback events that automatically update future profiles are not implemented. Neither are multi-source timelines, OTIO export, distributed cancellation, multi-user authentication, object storage, broad semantic labeling, or cloud API providers.

## Verification interpretation

The waveform correspondence measurement checks the raw source location of each matched speech span against the authored edit map. It is not a measurement of semantic understanding. Zero rounded median correspondence error is expected for copied source audio and does not imply perfect edits on other material.

The two non-training sessions were used in integration debugging, including correcting zero-duration ASR token assignment. Treat them as regression fixtures. A credible external benchmark should use new human recordings that have not influenced implementation, several creators, and blinded edit comparison.

## Release boundaries

The local product can process the user's own recordings. The hosted demo is read-only and labeled accordingly. Deployment access and hackathon submission must be reported separately from successful local builds and tests.
