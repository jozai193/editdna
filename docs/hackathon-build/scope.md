# EditDNA scope

Planning date: 2026-09-08. Status: architecture proposal, not implemented or validated.

## Product promise

Learn a creator's editing preferences from matching raw recordings and finished edits, then produce an editable first cut of new footage. The value is reduced correction time on each subsequent video, not a promised increase in views.

## Intended customer

A solo creator who repeatedly records single-speaker tutorials, explainers, or product reviews. They can supply source recordings and the corresponding final videos, or create those pairs. Channel accounts and analytics are unnecessary. Published videos alone cannot establish which alternatives the creator rejected.

## First build

- One camera, one speaker, English speech, ordinary cuts, and mostly unchanged source audio.
- Learn pause handling and selection between repeated takes; preserve ordinary content order.
- Import raw/final example pairs, inspect inferred matches, build an evidence-backed profile, edit unseen footage, review decisions, render MP4 and captions, and save the editable plan.
- Start with two to five distinct source sessions per demonstration profile; this is a proposed acquisition target, not a claim that five examples are statistically sufficient.
- Use a single source file per pair initially; internal identifiers permit multiple files later.
- Initial engineering limits: up to 20 minutes per source, 10 minutes per final, five pairs per profile, 2 GB per file, and one heavy local job at a time. Benchmark and reduce these limits if needed.

## Later expansion

Multiple cameras, matching B-roll to narration, introductions and story structure, visual layout learning, music preferences, speed changes, branded graphics, and team collaboration. These require additional observations, labels, and independent evaluation.

## Not claimed

An exact recreation of a creator's judgment, a foundation model trained from a handful of videos, guaranteed time savings, causal audience improvement, universal editor compatibility, or a unique invention established by competitor research.

## Data plan

The user confirmed: "Plan to create our own pairs." No paired creator dataset has been verified in this workspace. Create owned demonstration pairs. Two intentionally different demonstration profiles may be authored from training recordings, but must be labelled constructed preferences rather than real creator validation. New recordings must be held out for validation and testing. Availability of real creator pairs is a dependency for real creator claims, not for planning.

## Planning boundary

This folder is a separate project from E:\content engine (RetentionDNA). This task creates architecture documents only. Existing product code, deployments, and submissions are not altered. Implementation timing and the hackathon's live deadline must be checked before starting construction; the architecture is not a promise to finish the entire product within the remaining event window.
