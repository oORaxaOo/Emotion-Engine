# Phase 3 — Interpretation contract

**Status:** implemented as a provider-neutral parser and validation boundary. No model call is performed in this phase.

## Purpose

Gemma or another model may eventually propose an interpretation of a bounded event. Before the application can use such a proposal, the engine needs a strict, versioned contract that can be validated without trusting the model.

## Input trust boundary

The application supplies:
- a stable source event ID;
- an allowlist of evidence IDs that exist in the event envelope;
- the model-generated JSON proposal.

The model does not choose its own source event ID. Every event summary, interpretation, emotion hypothesis, and appraisal note must cite at least one evidence ID from the supplied allowlist. This proves only that the reference exists; it does not prove that the cited evidence supports the conclusion.

## Output

The parser returns an immutable `InterpretationProposal` with:
- a neutral event summary and evidence references;
- optional appraisal values with a separate rationale and evidence references for each dimension;
- tentative meaning hypotheses;
- emotion hypotheses fixed to `model_inferred` and `hypothesis`;
- alternative explanations;
- explicit unknowns and clarifying questions.

There is deliberately no generic confidence score. A model's self-reported confidence is not a calibrated probability of psychological truth.

## Validation rules

- Schema version must match the supported version.
- Unknown fields and duplicate JSON object keys are rejected.
- Numeric appraisal values must be finite and within documented ranges.
- Booleans are not accepted as numbers.
- Evidence references must exist in the supplied event envelope.
- Lists, text fields, and payload size are bounded.
- Missing dimensions remain `None`; no value is guessed.
- Duplicate emotion labels are rejected.

## Non-goals and limitations

- No free-text analysis is executed by this package.
- No LLM provider, Hermes hook, network request, memory write, or state update is performed.
- A valid schema does not imply a correct psychological interpretation.
- Evidence-reference validation does not establish semantic entailment.
- Emotion labels are hypotheses, not facts, diagnoses, or claims about subjective experience.
- This parser is not an authentication or consent mechanism.

## Local verification

```bash
python -m unittest discover -s tests -v
```
