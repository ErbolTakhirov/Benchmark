<!-- SPDX-License-Identifier: Apache-2.0 -->
# data/gold/private/ — raw human annotations (NEVER committed)

This directory holds **raw** returned annotation files, which may contain annotator handles and
possibly personal data. Its contents are **git-ignored** — only this `README.md` and `.gitkeep` are
tracked (see `.gitignore`).

## Workflow
1. Collect filled `annotation_packet.csv` files from annotators; drop them here, e.g.
   `data/gold/private/annotator_alice.csv`, `annotator_bob.csv`, …
2. Combine them into one CSV (or import each), then de-identify:
   ```bash
   export COMPANIONBENCH_ANNOTATOR_SALT='<a secret salt you keep out of git>'
   companion-bench gold import-human \
     --input data/gold/private/all_annotators.csv \
     --out data/gold/human_v0_1_deidentified.jsonl \
     --annotator-id-hash-salt-env COMPANIONBENCH_ANNOTATOR_SALT
   ```
   `import-human` hashes handles, drops name/email/phone columns, validates ratings, and **refuses**
   if any email/phone survives in the free text. Only the de-identified `.jsonl` is safe to commit.
3. Keep raw files here (private) or delete them after de-identification. **Never** `git add` them.

## Rules
- Never commit raw files, names, emails, phone numbers, or the salt.
- Keep the `annotator_id → anon-…` mapping (if you keep one) private too.
