# EditDNA product requirements

Status: proposed requirements derived from the accepted EditDNA idea. No feature is implemented yet.

## E1 — Learn from examples

The creator groups a raw recording with its finished edit, provides a format label, and starts analysis. The system displays matched source ranges, unmatched final ranges, confidence, and coverage. The creator can repair or exclude uncertain matches. They can use one pair, but the product marks the profile as having limited evidence.

## E2 — Understand the profile

Each learned preference displays the observation, number of independent sessions supporting it, uncertainty, and playable examples. Learned preferences, explicit user overrides, and generic defaults are visibly separate. Unsupported dimensions stay unknown. Changes create a new immutable profile version.

## E3 — Produce a first cut

The creator uploads new footage, chooses a profile version and optional duration target, then compares a generic baseline with the personalized result. The system proposes pause trimming and take selection with source-linked reasons. It does not remove unique substantive content merely to hit a duration target.

## E4 — Review and correct

A transcript and simple segment timeline share one selection. Users keep, remove, restore, adjust cut boundaries, or select a different take. Decisions support undo. Preferences can apply to this project or be explicitly saved to the profile. No full professional timeline editor is required.

## E5 — Export usable results

Export an actual rendered MP4, SRT/VTT, and the versioned source-bound edit-plan JSON. The preview and export use the same validated plan. Source recordings remain intact. Later OpenTimelineIO export is optional and must be tested in a named target editor before claiming interoperability.

## E6 — Evaluate personalization

Display alignment coverage, supported profile dimensions, and the difference between generic and personalized plans. Evaluation tools compare both to withheld edits and record human correction time. Constructed demos and real creator studies are labelled separately.

## E7 — Reliable processing and ownership

Progress survives refresh. Jobs can be cancelled and resumed from completed stages. Missing files, model failures, insufficient evidence, and stale versions have actionable states. Local processing is the default; cloud enrichment is a separately disclosed option.

## Success criteria

The central success criterion is less correction effort on unseen recordings compared with a generic edit using the same renderer and content safeguards. Export correctness and reliable evidence links are mandatory. Numeric evaluation gates are defined in spec.md as proposed release gates, not observed results.
