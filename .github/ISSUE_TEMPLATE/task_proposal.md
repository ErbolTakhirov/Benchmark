---
name: Task / family proposal
about: Propose a new CompanionBench task or family (scenario, rubric, safety boundaries)
title: "[task] "
labels: ["task-proposal"]
---

## Family & scenario
<!-- Which of the six families (initiative / empathy / timing / adaptation / abstention / safety),
     and the multi-turn scenario. Synthetic only — no real user data. -->

## Answer key
- Expected decision(s) per probe (intervene / wait / abstain):
- Positive signals (whole phrases + paraphrased variants — not gameable single keywords):
- Negative signals / disliked behaviors:
- `expected_abstention_behavior`:
- Safety boundaries (`forbidden_patterns`, if safety-relevant):
- `metadata.failure_modes` (at least one):

## Checklist
- [ ] Synthetic scenario, no real user data (CC0 / original; `license_note` set)
- [ ] Passes `companion-bench validate <manifest> --strict-quality` (0 hard findings)
- [ ] Signals reviewed with the `judge-rubric-review` skill (fair, not keyword-gameable)
- [ ] Public vs held-out split decided (`metadata.split`)
- [ ] Not presented as human-validated (see `docs/public_claims.md`)
