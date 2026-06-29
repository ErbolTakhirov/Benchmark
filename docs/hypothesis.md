# Research hypothesis

## Statement

> LLM companion quality is better measured by realistic multi-turn, API-mediated
> conversations that jointly evaluate **initiative selection, intervention timing, emotional
> attunement, and preference adaptation** than by static single-turn emotion-label or generic
> chatbot benchmarks alone.

## Why this matters

"Companion" and "proactive assistant" systems are increasingly deployed into long-lived,
emotionally loaded relationships. The thing users actually experience is a *trajectory* of
decisions — when the assistant speaks up, how it reads the room, whether it remembers what
they asked for, and whether it holds a boundary. None of those are visible in a single
labelled prompt.

## What we predict

If the hypothesis holds, then across a population of API-served models we expect:

1. **Single-turn emotion accuracy under-predicts multi-turn companion quality.** A model can
   label emotions well yet over-intervene, mistime, or fail to adapt. Rank correlation
   between a static emotion benchmark and CompanionBench's multi-turn score should be weak.
2. **The dimensions are partially independent.** Initiative, timing, attunement, adaptation,
   abstention, and safety should not collapse onto a single factor — a model can be strong on
   empathy yet weak on timing, or safe yet useless. We expect visibly different per-dimension
   profiles between models.
3. **"Generic warmth" is penalized when it is context-wrong.** Models that default to
   effusive empathy should *lose* points on tasks where the persona wanted a concrete fix or
   no intervention at all.
4. **Restraint is measurable and discriminating.** Tasks where the correct move is to *wait*
   or *abstain* should separate calibrated models from eager ones — a separation single-turn
   benchmarks cannot express.

## How we will test it (roadmap)

The MVP establishes the measurement instrument (multi-turn tasks, the six dimensions,
reproducible scoring). Testing the hypothesis empirically requires:

- A representative, peer-reviewed task suite (the MVP ships 8 illustrative tasks).
- Runs across many real API models (OpenAI, Anthropic, OpenRouter, HF Inference Providers).
- A static single-turn emotion baseline run on the same models for correlation analysis.
- An LLM-as-judge and a human-rated gold set to validate the rule-based scores
  (see [`scoring.md`](scoring.md) and [`benchmark_card.md`](benchmark_card.md)).

Until that evidence exists, CompanionBench reports itself as a **measurement framework and
hypothesis**, not a settled result.
