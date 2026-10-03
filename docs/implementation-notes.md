# Assignment execution notes

Source requirements: W15_Assignment.pdf, W16_Assignment.pdf, W17_MLOps_Assignment.pdf, and the supplied W15–W17 implementation plan. Existing workspace projects/scaffolds were not read or used. Tracks are separate private repositories under shkroyas. Solo authorship: Royas Shakya; no collaborating development agents were used.

The plan's example results are not copied as evidence. Initial from-scratch work is organized into requirement-specific commits within an integration PR for each track; this consolidates interdependent bootstrapping work. Real Track B prompt experiments must each use a new experiment PR and a genuine prior development failure trace. No speculative draft is labeled a completed experiment. GitHub submission/final tags are conditional on checks; Track B remains an implementation draft until live evidence exists.

Track A core workflow and bonus DAG are executed locally. Stage transitions use pinned MLflow 2.22.2, with aliases for serving. The optional cloud deployment in W15 belongs to the assistant rather than this CPU pipeline. An independent Docker run comparison, if generated, is stored under reports/container_validation instead of overwriting the original local run references.

GitHub setup applied: private repository, squash-only merges, automatic head-branch deletion, main protected with required ci check/PR/linear history, force pushes and branch deletion blocked, all planned labels, one milestone and linked implementation issue per track. PR #1 consolidates the from-scratch bootstrap.
