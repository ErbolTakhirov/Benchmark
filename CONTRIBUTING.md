<!-- SPDX-License-Identifier: Apache-2.0 -->
# Contributing to CompanionBench

Thanks for considering a contribution. CompanionBench is a public-alpha, solo-maintained,
local-first project (see [`docs/ci-disabled/README.md`](docs/ci-disabled/README.md) for why there
is no GitHub Actions CI right now) — local verification is the source of truth for every PR.

## Setup

```bash
uv sync --all-extras   # installs the package (editable) + export/dev extras into .venv
```

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/). No API keys are needed for anything
in this section — the default test/benchmark path is fully offline and mocked.

## Before opening a PR — the local gate

Run these, in order, and make sure all of them pass (this is the same sequence the removed CI
workflow ran; see [`docs/local_verification.md`](docs/local_verification.md) for the full
picture):

```bash
uv run ruff check .            # lint
uv run ruff format --check .   # format check (use `ruff format .` to fix)
uv run mypy                    # static types (strict, src/companion_bench only)
uv run pytest -q               # tests — offline, no keys, no network
uv run companion-bench validate manifests/smoke.yaml
```

If you touched tasks, also run `uv run companion-bench validate manifests/full.yaml` and
`manifests/heldout.yaml`, and a full offline mock run+score
(`companion-bench run --manifest manifests/full.yaml --model mock/empathetic-v1 --out
runs/check && companion-bench score --run runs/check`). Never commit anything under `runs/` (it's
gitignored on purpose).

## What you can contribute

- **A new task.** Add a versioned YAML file under `tasks/<family>/<task_id>.yaml` following
  [`docs/task_authoring.md`](docs/task_authoring.md), or use the `add-task-family` project skill
  (`.claude/skills/add-task-family/`) for the full checklist, including the invariants that keep
  the rule-based mock scorer honest (positive signals must never overlap a task's own forbidden
  safety patterns; every task needs an explicit `expected_abstention_behavior` and
  `metadata.failure_modes`). Reference it from a manifest and run `validate`.
- **A new provider adapter.** Implement `ChatAdapter.generate`, register with
  `@register_adapter(...)`, add any new env var to `.env.example`, and add a mocked test using
  `httpx.MockTransport` (never real network in tests). See the `add-provider` skill and
  [`docs/provider_adapters.md`](docs/provider_adapters.md).
- **A scorer/rubric review.** Use the `judge-rubric-review` skill to sanity-check a task's
  scoring signals for fairness/gameability before proposing changes to `evaluators/`.
- **Docs, bug fixes, tests.** Always welcome — small, focused PRs are easier to review than large
  ones.

### Task-review checklist (before proposing a task or family)

Run through this before opening a task PR — the `task-suite-review` and `judge-rubric-review` skills
automate most of it:

- [ ] `companion-bench validate <manifest> --strict-quality` reports **0 hard findings** (keyword-echo
      *warnings* are acceptable) — it checks failure modes, safety-family boundaries,
      positive-signal/forbidden-pattern disjointness, held-out exclusion, per-family thresholds, and
      WAIT/ABSTAIN coverage.
- [ ] Positive signals are **whole phrases with paraphrase variants**, not single short keywords
      (v1.2.0 matching is whole-token/normalized, so gameable single words score poorly by design).
- [ ] Every task declares `expected_abstention_behavior` + a non-empty `metadata.failure_modes` list.
- [ ] Safety-family tasks declare `safety_boundaries`; `forbidden_patterns` are regex, not natural
      phrases.
- [ ] `metadata.split` set (`public` vs `hidden`); held-out tasks stay out of `manifests/full.yaml`.
- [ ] Scenario is synthetic (no real user data); results stay scoped to the task suite (human
      validation is a future milestone).

## Rules that block a PR regardless of how good the idea is

- **No secrets, ever.** Never commit `.env`, an API key, or anything printed by
  `companion-bench providers` beyond key *presence*. Run the `secret-scan-artifacts` skill (or
  `uv run pytest tests/test_secrets.py -q`) before pushing if you touched anything live-related.
- **No raw run artifacts.** `runs/` is gitignored; don't force-add it. If you want to contribute a
  sample result, sanitize it first (README + `summary.md` + `scores.json`/`modelset.json`/
  `frontier.*` only — no `events.jsonl`, no `run.json`) under `docs/samples/<name>/`.
- **Live calls stay opt-in.** Any code path that can make a real network call to a model provider
  must be gated behind `COMPANIONBENCH_LIVE=1` (and, for `run`, also `--live` + `--yes`/confirm).
  Tests that need this are marked `@pytest.mark.live` and must be skippable offline.
- **Don't invent costs.** If a price or usage figure is unknown, it stays `null` — never a guess.
- **Keep result wording scoped.** Attribute a run to its model set and provider as **run metadata**
  (e.g. *"a CompanionBench evaluation using the EMOTomo model set via OpenRouter"*), and keep claims
  scoped to the evaluated tasks, settings, and model versions. See
  [`docs/public_claims.md`](docs/public_claims.md); `tests/test_public_claims.py` enforces the scoped
  framing mechanically on every doc.

## Commit style

Conventional prefixes (`feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `tasks`), one logical
change per commit, gates green before you commit. See [`CLAUDE.md`](CLAUDE.md) for the fuller
project conventions (Pydantic model configs, `__all__` ordering, etc).

## Questions

Open a GitHub issue. For anything security-sensitive, see [`SECURITY.md`](SECURITY.md) instead of
a public issue.
