# Human editing pilot

Open http://localhost:3000/trial. Read the task brief before starting. The first participant edits manually, then with the learned profile. Later participant sessions alternate the order. This is descriptive counterbalancing, not random assignment.

Each condition edits a different constructed tutorial of similar complexity: eight unique instructions, two repeated takes, long pauses, and the same framing target. Sources and transcripts are preloaded. Training/transcription time is excluded and must be disclosed alongside any result. The timer includes edit generation, adjustments, rendering, and full-output playback review. Do not pause, reload to evade elapsed time, or work on another task during a run.

Finish requires a current rendered revision, eight reference-aligned segments within 180 ms, framing within 0.01 of 1.10×, and the participant's confirmation of full playback and usable quality. A failed quality check keeps the timer running. Negative savings are valid. The timer and result are persisted in the local SQLite store and downloadable as JSON.

Report manual and assisted seconds, difference, condition order, source durations, prior familiarity, and any interruptions. Describe the result as a one-person controlled pilot on synthetic footage. Never extrapolate to all creators or audience retention. Do not use automated QA times as participant evidence.
