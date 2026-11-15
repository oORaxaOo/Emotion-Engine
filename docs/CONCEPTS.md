# Concepts and Research Foundations

**Status:** initial working vocabulary. Definitions will evolve as research and tests develop.

## 1. Why a list of emotion words is insufficient

The same external event can be interpreted differently by different people, or by the same person in different contexts. Therefore an event should not map directly to one fixed emotion label.

Emotion Engine should represent the chain between an event, its interpreted meaning, its appraisal, and a possible emotional description. Each step can be uncertain or incomplete.

## 2. Keep four things separate

### 2.1 Event

A bounded description of what happened. It should distinguish reported facts from assumptions.

### 2.2 Appraisal

An interpretation of what the event means in relation to goals, needs, expectations, relationships, control, and values. Appraisals are subjective hypotheses, not objective properties of the event.

### 2.3 Affect coordinates

A compact, optional representation of broad affective dimensions. The initial research candidate is the circumplex approach:

- **Valence:** unpleasant to pleasant.
- **Arousal:** low activation to high activation.

These coordinates are simplifications. They do not fully describe an emotional episode and must remain optional.

### 2.4 Emotion label

A human-language category such as disappointment, relief, anger, or joy. Labels may overlap, be mixed, or be unavailable. A label inferred by a model must never overwrite a label directly reported by the person.

## 3. Appraisal dimensions

The initial catalogue should use a small number of interpretable dimensions, informed by appraisal research:

- **Relevance:** does the event matter to the person or their social group?
- **Implications:** what consequences may follow, and how do they relate to short- and long-term goals?
- **Coping potential:** how much control or capacity does the person believe they have?
- **Normative significance:** how does the event relate to personal standards, identity, social norms, or values?

Possible lower-level attributes include novelty, expectedness, goal congruence, causal attribution, urgency, controllability, and perceived fairness.

Not every field must be present. Missing information must remain unknown rather than being filled with guesses.

## 4. Multiple theories, not one universal answer

The initial research shelf should include, at minimum:

- **Circumplex model of affect:** useful as a compact dimensional representation of affect.
- **Component Process Model / appraisal approaches:** useful for structuring event relevance, implications, coping potential, and normative significance.
- **Constructed emotion theory:** useful as a distinct perspective on how emotion categories relate to prediction, bodily regulation, and categorisation.

These approaches are not interchangeable and are not a single agreed theory. The knowledge base should record each theory's claims, scope, evidence, criticisms, and versioned references separately.

## 5. Evidence and provenance vocabulary

Every claim must carry an origin:

- **user_reported** — explicitly stated by the user.
- **system_observed** — derived from a concrete software event or measured state.
- **model_inferred** — proposed by an LLM and not independently established.
- **human_confirmed** — explicitly reviewed and confirmed by the user or an authorised operator.

Every interpretation also needs an epistemic status:

- **confirmed**
- **observed**
- **hypothesis**
- **disputed**
- **unknown**

A model-generated hypothesis must never be silently upgraded to confirmed.

## 6. Working rule for ambiguous cases

Prefer:

> The event may have involved disappointment because an expectation appears to have been unmet. The expectation and its importance have not yet been confirmed.

Avoid:

> You are disappointed because you need recognition.

The first is a bounded hypothesis with visible uncertainty. The second invents an internal cause and states it as fact.

## 7. Research references

1. Russell, J. A. (1980). *A Circumplex Model of Affect*. Journal of Personality and Social Psychology, 39(6), 1161–1178. https://doi.org/10.1037/h0077714
2. Posner, J., Russell, J. A., & Peterson, B. S. (2005). *The circumplex model of affect: An integrative approach to affective neuroscience, cognitive development, and psychopathology*. Development and Psychopathology, 17(3), 715–734. https://doi.org/10.1017/S0954579405050340
3. Scherer, K. R. (2001). *Appraisal Considered as a Process of Multilevel Sequential Checking*. In *Appraisal Processes in Emotion: Theory, Methods, Research*. https://doi.org/10.1093/oso/9780195130072.003.0005
4. Barrett, L. F. (2017). *The theory of constructed emotion: an active inference account of interoception and categorization*. Social Cognitive and Affective Neuroscience, 12(1), 1–23. https://doi.org/10.1093/scan/nsw154

5. Scherer, K. R. (2009). *Emotions are emergent processes: they require a dynamic computational architecture*. Philosophical Transactions of the Royal Society B, 364(1535), 3459–3474. https://doi.org/10.1098/rstb.2009.0141

This paper is especially relevant to the project's computational modelling question: it discusses dynamic architectures for modelling emotion-related processes in virtual agents. It is a design and theory contribution, not evidence that a virtual agent has subjective experience.

These are starting points for a research catalogue, not proof that any one model is complete or universally accepted.
