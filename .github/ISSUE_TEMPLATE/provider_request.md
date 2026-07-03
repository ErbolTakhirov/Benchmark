---
name: Provider adapter request
about: Request or propose a new provider adapter
title: "[provider] "
labels: ["provider"]
---

## Provider
- Name / API:
- OpenAI-compatible endpoint? (yes / no)
- Auth env var (name only — **never** paste a key):

## Notes
<!-- See docs/provider_adapters.md and the `add-provider` skill. Adapters MUST ignore
     `simulation_context` (that field is for the mock only) and be tested with httpx.MockTransport —
     no live network calls in tests, no hard-coded keys. -->
