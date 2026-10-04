# Project demonstration and narration

[Watch or download week17-task-a-b-core-demo.mp4](https://github.com/shkroyas/w17-trackA-churn-mlops/releases/download/w17-trackA-final/week17-task-a-b-core-demo.mp4) (**9m45s**) explains both separate projects. The [extended Azure demonstration](https://github.com/shkroyas/w17-trackA-churn-mlops/releases/download/w17-trackA-final/week17-task-a-b-complete-demo.mp4) is **10m53s**. These combined assets are on Task A's private release and require repository access.

## What the core video explains

| Start | Chapter |
|---|---|
| 0:00 | Two independent Week 17 projects |
| 0:40 | Reproducibility and repository organization |
| 1:28 | Task A: experiment comparison and selection |
| 2:20 | Task A: real registry-backed prediction |
| 2:58 | Task A: native data, target and custom drift reports |
| 3:51 | Task A: drift does not automatically authorize promotion |
| 4:37 | Task B: a live adaptive verification query |
| 5:30 | Task B: full trajectories and trace-driven revisions |
| 6:17 | Task B: completed experiments and production choice |
| 7:13 | Task B: native judging, calibration and limitations |
| 8:09 | Task B: healthy regression and explicit infrastructure failure |
| 8:55 | Submission evidence and the limits of this demo |

The extended video inserts the actual authenticated Azure browser demonstration before the final handoff. The core version includes actual local predictions, invalid-input checks, sourced Qwen execution, validated cache reuse, native tracking/drift/judge reports and Airflow execution evidence. Source-derived cards explain recorded experiment decisions and limitations. Local Airflow footage is separate from Azure application hosting.

## Clearer narration revision

The revised videos use the **en-US-GuyNeural** synthetic English voice through [edge-tts 7.2.8](https://github.com/rany2/edge-tts), at a slightly slower **−5%** rate. This replaces the earlier Flite voice. It is neural synthesis, not a recording or clone of a person's voice. The demo scripts contain no provider credentials, and narration uses no Groq, Gemini, Qwen or cloud deployment quota.

Volume is normalized to a −18 LUFS target with a −1.5 dBTP ceiling and encoded as AAC at 160 kbps. Captions follow speech-service word timing and retain transcript punctuation. Existing recorded footage is retimed to the new speech; the handoff card now reports the current 80-test Task B suite. Original experiment reports, quality gates and implementation-final tags are unchanged. This narration edit does not constitute a new full model evaluation.

Both videos passed full audio/video decoding. Caption intervals, chapter order, duration and checksums were checked. Earlier Flite recordings remain archived locally at `demo-video/archive/flite-20261004/`; the historical cloud-outage recording is retained separately. Earlier handoff provenance records the original narration hashes. Use the current manifests below to verify the revised video files.

## Downloadable supporting files

- [Core transcript](https://github.com/shkroyas/w17-trackA-churn-mlops/releases/download/w17-trackA-final/TRANSCRIPT.md), [core SRT captions](https://github.com/shkroyas/w17-trackA-churn-mlops/releases/download/w17-trackA-final/week17-core-demo.srt), [core chapters and SHA-256](https://github.com/shkroyas/w17-trackA-churn-mlops/releases/download/w17-trackA-final/core-video-manifest.json).
- [Extended transcript](https://github.com/shkroyas/w17-trackA-churn-mlops/releases/download/w17-trackA-final/COMPLETE_TRANSCRIPT.md), [extended SRT captions](https://github.com/shkroyas/w17-trackA-churn-mlops/releases/download/w17-trackA-final/week17-complete-demo.srt), [extended chapters and SHA-256](https://github.com/shkroyas/w17-trackA-churn-mlops/releases/download/w17-trackA-final/complete-video-manifest.json).
- [Narration revision and old/current hashes](https://github.com/shkroyas/w17-trackA-churn-mlops/releases/download/w17-trackA-final/narration-revision.json).

Current core SHA-256: `6bdaefbbf6ae173817a445aaccea87e1b17f0d1a4821e17eda4682be6de48003`.

Current extended SHA-256: `bbb98293a54a3a0c2a207fee51db24a395731cc5a9816d92d1d1d14b787e6a14`.
