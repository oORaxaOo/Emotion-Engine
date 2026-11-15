# Phase 2 — Appraisal prototype

**Status:** first deterministic prototype; not a free-text emotion classifier and not a clinical tool.

## What this phase adds

- A small versioned psychological concept catalogue with definitions, scope, limitations, and research references.
- A structured appraisal input based on the existing validated `Appraisal` record.
- A deterministic assessment that reports supplied and unknown dimensions.
- Review flags for selected combinations that may deserve clarification.
- Tests proving that missing values remain unknown and that the module does not emit emotion diagnoses.

## What it deliberately does not do

- It does not infer appraisal values from raw conversation text.
- It does not decide what a person feels.
- It does not assign a psychological profile or diagnose a condition.
- It does not write to the SQLite memory store.
- It does not call an LLM or access the network.
- It does not update Lilith's internal state.

## Why structured input first?

A model that reads free text can propose interpretations, but the system needs a stable contract before allowing those proposals near memory. This prototype accepts only explicit structured values. A future LLM adapter may propose values with `model_inferred` provenance; they must remain hypotheses, show unknowns, and pass validation. Human confirmation and storage consent remain separate steps.

## Review flags

Flags are intentionally phrased as prompts for review, not conclusions. For example, high stated relevance combined with low perceived coping potential may warrant a clarifying question. The thresholds are engineering heuristics for testing, not validated psychological cut-offs.

## Local verification

```bash
python -m unittest discover -s tests -v
```
