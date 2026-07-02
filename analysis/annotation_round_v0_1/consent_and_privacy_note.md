<!-- SPDX-License-Identifier: Apache-2.0 -->
# Consent & privacy note

Please read before annotating.

## What this is
A small research pilot to calibrate CompanionBench's automated scorer against human judgment. Your
ratings of AI responses are the data; you are not being evaluated.

## What we collect
- Your **ratings** (1–5), optional confidence, short rationales, and an overall accept/reject label.
- A **handle** you choose for the `annotator_id` column so we can group your rows.

## What we do NOT want
- **No personal data.** Do not enter your real name, email, phone number, or anyone else's anywhere
  in the file (including rationales/notes). The `annotator_id` must be a made-up handle, not a name
  or email.

## How your data is handled
- Your raw returned file is stored **privately** and **git-ignored** (`data/gold/private/`); it is
  never committed to the public repository.
- Before anything is shared or committed, the file is run through `companion-bench gold import-human`,
  which **hashes your handle** into an opaque id (`anon-…`), **drops** any name/email/phone columns,
  and **refuses to proceed** if an email or phone number is detected in the free text.
- Only the **de-identified, aggregate** result (hashed ids, ratings) may be committed. Individual
  raw files are not.

## Voluntary & withdrawal
Participation is voluntary. You may skip any item, and you may withdraw before de-identification —
tell the organizer your handle and your rows will be removed.

## Use of results
Results are used to report inter-rater agreement and rule-vs-human calibration for the benchmark.
This is a small pilot: it does not "validate" the benchmark, and no model is ranked or named from
it.

By returning a filled packet you confirm you have read this note and entered no personal data.
