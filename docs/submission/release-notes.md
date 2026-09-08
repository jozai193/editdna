EditDNA learns recurring edits from reviewed raw-to-final examples and applies them to a new recording.

This release includes the complete local engine and editor, five owned demonstration sessions, two trained preference profiles, six real rendered outputs, screenshots, and a 2-minute narrated walkthrough.

Working preferences: pause spacing, exact-transcript equivalent-take selection, and fixed centered framing. Every cut remains reviewable. Graphics, grading, crop timing, narrative rearrangement, and retention prediction are outside this release.

Validation: 21 automated tests; application lint, TypeScript, and production build; browser profile/example/output checks; fresh-workspace restore; actual output-frame checks recover the applied 1.00× and 1.10× crops. The synthetic regression corpus is described in the README. No human time-saving percentage is claimed.

Download `editdna-source.zip`, extract it, and follow the Windows setup instructions in README.md. The first local transcription downloads the speech model. The source repository includes all files as well.

`editdna-demo.mp4` uses real application captures, synthesized narration, and an actual rendered edit. It is an edited walkthrough, not an uncut live screen recording.
