# Research and Evaluation Plan

**Status:** proposed research method. No experiments have been run.

## 1. Research question

Can a local system combining event appraisal, user-controlled memory, explicit internal computational state, and bounded self-observation produce useful, novel, persistent, and reproducible behaviour beyond a baseline assistant?

This is a question about observable system behaviour. It is not a test for consciousness or subjective experience.

## 2. Operational meaning of emergence

For this project, a behaviour may be labelled a **candidate emergent behaviour** only when:

1. it is not a direct, hard-coded response rule for the exact test input;
2. it arises from the interaction of at least two documented components;
3. the causal contribution of those components can be tested by disabling or changing them;
4. it can be reproduced under recorded conditions, or its variability is explicitly reported;
5. the behaviour is useful or meaningfully different according to a defined evaluation.

Not being hard-coded as one explicit rule does not mean uncaused, alive, or conscious.

## 3. Initial hypotheses

- **H1 — Context-sensitive appraisal:** structured appraisal dimensions will distinguish events that share surface wording but differ in context.
- **H2 — Memory-informed interpretation:** user-approved event memories will improve continuity on relevant future tasks without causing unrelated memories to leak into responses.
- **H3 — Corrective self-observation:** structured comparison between an action and its observed outcome will help identify repeatable error classes without treating model-generated motives as facts.
- **H4 — Evidence-seeking question cascade:** a bounded sequence in which each generated question is investigated using newly collected evidence may uncover progressively deeper operational causes without recycling unsupported hypotheses.
- **H4 — Component interaction:** combining appraisal, memory, state, and self-observation may create stable behaviours not present in isolated components.

Each hypothesis must be testable and may be rejected.

## 4. Baselines and ablations

Compare at least these configurations:

- baseline model without Emotion Engine;
- appraisal only;
- appraisal plus memory;
- appraisal plus internal state;
- appraisal plus self-observation;
- full bounded system;
- full system with one component disabled at a time (ablation).

A result that disappears when a component is disabled gives evidence about that component's contribution. It does not prove subjective experience.

## 5. Evaluation measures

Possible measures include accuracy of extracting explicitly reported emotions, separation between user reports and model hypotheses, quality of alternative interpretations and unknowns, precision of relevant memory retrieval, rate of irrelevant memory insertion, frequency of unsupported causal claims, repeat-error detection and correction rate, state drift and invalid transitions, reflection-loop count and budget enforcement, and reproducibility across repeated runs.

Do not create a single consciousness, sentience, or emotion-authenticity score.

## 6. Experiment controls

- Start with synthetic or deliberately non-sensitive fixtures.
- Record software version, model/provider version, prompt/schema version, configuration, and random seed when available.
- Repeat each test enough times to expose variability.
- Keep baseline and experimental inputs identical.
- Review both successful and failed examples.
- Use ablation tests to test causal contribution.
- Keep raw personal conversations out of research fixtures unless there is a separately approved, privacy-safe protocol.

## 7. Failure conditions

A feature is not ready if it confuses an inference with a user-confirmed report, stores emotional information without approval, retrieves unrelated memories in a way that changes the answer, creates unbounded recursive reflection, repeatedly reinforces its own unsupported hypothesis, makes clinical or consciousness claims from its own generated text, or cannot explain which records and state transitions influenced an output.

## 8. Reporting

Every experiment report should state the question and hypothesis, tested configurations, input and software versions, observations and measurements, failures and counterexamples, and what cannot be concluded.

A negative result is useful. The project must not tune experiments merely to obtain evidence for a preferred conclusion.
