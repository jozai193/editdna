# EditDNA planning notes

## 2026-09-08 — Architecture proposal

- User selected the idea of learning a personal editing style from raw-to-final pairs and requested the entire architecture before implementation.
- Created scope.md, prd.md, and spec.md as a coherent planning package. No application code, model training, dependency installation, deployment, or submission performed.
- Defaults proposed by the assistant: single-speaker English tutorials/reviews, React UI, Python backend/worker, local processing, statistical learning first, optional cloud semantics, hosted judge mode later.
- Stack and deployment defaults are proposals, not user confirmations. The user confirmed the data choice: "Plan to create our own pairs." Added a five-session acquisition plan with two constructed profiles, session-level splits, hidden reference edits, and explicit limits on validation claims.
- Applied the technical-spec skill's structure and dependency guidance. The workspace had no guided-flow state or upstream documents; the user's direct request for a complete architecture was handled without forcing registration or a staged onboarding detour. No event registration/terms state was fabricated.
- Memory informed source-bound export and the distinction between verified mechanics and outcome claims; no RetentionDNA code or files were copied or changed.
- Central decision: alignment quality gates precede preference learning, and held-out personalization tests precede UI polish.
- Next engineering action: implement Gate A against a small owned raw/final pair after checking current deadline and dataset availability. This is a recommendation, not work started.

## 2026-09-08 — Local implementation and release checks

- Built the local media engine, FastAPI service, persistent queue, versioned profiles, and React review workspace. Actual MP4 rendering and caption/plan exports work.
- Generated five owned synthetic tutorials and ten constructed reference edits. Training consumes only the first three source sessions. Learned pause targets are 0.11 and 0.61 seconds; first/last repeated-take preferences have six observations each across three sources.
- Regression evaluation: 50/50 accepted source correspondences within 100 ms; all 16 held-out take decisions match the constructed references; pause target error 5 ms versus 235–265 ms for the generic setting. Held-out sources were used in integration debugging, so this is not a sealed benchmark.
- Fixed video-frame padding drift, zero-duration ASR-token assignment, job/export ID collisions, pending-job reuse, and undo history behavior. Added media type/protocol checks, same-origin mutation restrictions, source bounds, locks, and revision conflicts.
- 17 automated tests pass, including a real FFmpeg decode/timing test. An isolated HTTP release check passes create-plan, lock, undo, background render, six artifact downloads, VTT, and byte-range media requests.
- Upgraded the generated starter to patched compatible dependencies; npm audit reports zero vulnerabilities. The authored application lint and TypeScript checks are separate from upstream catalog lint.
- Added startup/stop/setup scripts, restoreable demo data, source bundle, README, implementation status, and a demonstration walkthrough.
- Hosted publication is blocked by a Sites connection/account mismatch: the previously created EditDNA project returns NOT_FOUND, while the currently visible account lists other projects. Preserved the original site ID and asked the user to reconnect the original account. No site recreation or unrelated site mutation performed.

## Visual learning and public release

- Implemented fixed centered framing estimation and review across corresponding frames; the learner requires three independent sources. It recovered 1.00x and 1.10x on the constructed corpus. Independent checks of actual rendered frames recovered both applied crops.
- Added a server-timed human editing pilot with a quality gate and no fabricated savings. It is prepared; participant results are pending.
- 21 tests pass. Application lint, TypeScript, build, desktop/mobile browser checks, fresh restore, and public demo-data access pass.
- Sites access was restored, private publication succeeded, and the user explicitly approved making EditDNA public. URL: https://editdna-studio.adityajevoor.chatgpt.site
- Public source and narrated walkthrough: https://github.com/jozai193/editdna/releases/latest
- Submission write-up is prepared. No Devpost submission was performed.
