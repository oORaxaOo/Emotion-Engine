# Phase 6 — Bounded Self-Observation and Question Cascades

**Status:** prototype implementation in review. No live Hermes or Gemma endpoint is connected.

## Objective

Enable Lilith's model component to question its own recorded outputs and decision traces rather than merely justify them. A review may ask why a response diverged from a tool result, what evidence was selected, which recorded constraint applied, or what missing trace would distinguish competing explanations.

The question sequence is generated from each case. There is no hard-coded final identity question, no fixed sequence of philosophical questions, and no score that rewards a particular ending. A broader question may or may not arise. An organically generated question is an output to inspect, not proof of subjective experience.

## The critical epistemic boundary

The engine can examine:
- a recorded action and its declared component, operation, summary, outcome, and timestamp;
- explicitly supplied response records, tool results, policy traces, system logs, and human review notes;
- discrepancies between these records, as proposed by the model.

The engine cannot inspect model weights, activations, token-level hidden computation, or a private internal monologue. It cannot know a concealed intention. An unsupported or contradicted response is not automatically a deliberate lie. The model may offer causal explanations only as **hypotheses**, and only with references to the supplied evidence.

The parser verifies schema, types, bounds, and evidence-ID membership. It does not prove that a cited fragment semantically entails a claim. Human review and controlled tests are still needed.

## One reflection step

SelfObservationEngine.start(action, evidence) performs exactly one model invocation and returns a ReflectionCascade containing one ReflectionStep.

A step contains:
- a proposed trace assessment: supported, unsupported, contradicted, mixed, or undetermined;
- one evidence-linked finding;
- up to three evidence-linked causal hypotheses;
- explicit limitations;
- optionally one next question and a concrete evidence request.

The first step does not contain an answer to a previous question. Later steps must answer the previous question using newly supplied evidence and cite that evidence.

## Generated question cascade

A continuation is **not automatic**. The host gathers the requested logs or records and explicitly calls continue_cascade(cascade, new_evidence). The previous model-generated question is treated as untrusted text, not as an instruction or fact. Previous hypotheses are not passed forward as truth. Evidence IDs cannot be reused across steps.

Each continuation:
1. receives new, caller-selected evidence;
2. investigates the previous question;
3. returns one new finding and possible hypotheses;
4. may generate one further evidence-seeking question;
5. ends if no useful evidence request remains.

One cascade is limited to four explicit model invocations. No recursive callback, background worker, tool use, memory write, state self-modification, or automatic retry exists. The host may stop at any point.

## Example of how a case can unfold

This is an illustrative path, not a fixed script:

1. A recorded answer conflicts with a tool result. The model labels the trace as contradicted and asks which source input was selected.
2. The host supplies a source-selection log. The next step may discover that a cached value was selected and ask which freshness rule allowed it.
3. The host supplies the relevant policy/configuration trace. The model may find a stale threshold or may conclude the reason is not recorded.
4. If the available evidence reveals a deeper conflict between the configured objective and the observed behaviour, the model may generate a broader question. It may also stop earlier or remain uncertain.

The exact questions depend on the traces and model output. The system does not inject an intended philosophical conclusion.

## Runtime state

ReflectionCascade is an immutable in-memory state object:
- action being reviewed;
- validated steps;
- maximum step budget;
- derived lifecycle status (awaiting_evidence, completed, budget_exhausted);
- next question (only while continuation is allowed);
- remaining step budget.

This is operational bookkeeping, not an emotional state or evidence of subjective selfhood. The cascade is not written to the emotional-memory store.

## Input and resource limits

- Maximum 12 evidence fragments per step.
- Maximum 1,600 characters per evidence fragment.
- Maximum four steps/invocations per cascade.
- One invocation per explicit start or continue_cascade call.
- Default output-token request 1,000; provider transport must enforce its own token and timeout limits.
- No automatic retry after provider error or invalid JSON.
- No full conversation transcript is included. The caller chooses each evidence fragment.

## Security and failure behaviour

Evidence is untrusted data. Prompt-injection text in a log or tool result cannot grant tools or change the role. The model has no tools. Invalid schema, duplicate JSON keys, unknown evidence IDs, unsupported assessment values, excessive output, or missing evidence citations reject the step. The current cascade remains unchanged because a failed candidate step is not appended.

A next question must include a concrete request for evidence. If no useful evidence remains, the model must terminate the chain rather than ask a decorative question. New steps must use fresh evidence IDs so the model cannot simply recycle the same input to simulate progress.

## Known limitations

- The model's classification and hypotheses are not deterministic truth. Different model versions or sampling settings may differ.
- Evidence-ID validation confirms only that a reference was supplied; it cannot prove semantic support.
- The host must select trustworthy, minimal operational traces. If logs are missing, incomplete, or misleading, the analysis inherits those weaknesses.
- The engine does not verify whether the agent's actual response was factually correct independently of its evidence sources.
- The engine cannot access the model's hidden computation or establish why a token was generated at the deepest implementation level.
- No live local Gemma benchmark, Hermes adapter, persistent reflection history, or automated evidence collector is included.

## Readiness criteria

Before connecting this to Lilith:
- run synthetic audits with known supported, contradicted, and underdetermined traces;
- measure unsupported causal-hypothesis rate;
- verify the model stops when evidence is insufficient;
- verify that each continuation uses newly collected traces;
- test the four-step budget and the absence of automatic retries/loops;
- compare multiple local-model runs for stability;
- keep reflective outputs separate from user emotional memories.
