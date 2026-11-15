# Phase 4 — Bounded model adapter

**Status:** provider-neutral one-shot adapter implemented. No concrete provider, Hermes hook, or live Gemma endpoint is configured by this package.

## Purpose

Phase 3 established the output contract. Phase 4 adds a narrow bridge between a caller-supplied text-generation function and that contract.

The adapter:
1. Accepts one source event and a small, explicitly selected list of evidence fragments.
2. Builds a bounded prompt that labels evidence as untrusted data.
3. Invokes the injected text generator exactly once.
4. Passes output through the Phase 3 parser.
5. Returns an immutable, ephemeral interpretation proposal.

## Limits

Defaults:
- at most 12 evidence fragments;
- at most 1,200 characters per evidence fragment;
- at most 12,000 prompt characters;
- at most 1,200 requested output tokens;
- at most 28,000 response characters;
- a requested transport timeout of 45 seconds.

The adapter passes the token cap and timeout to the injected transport. The transport implementation must enforce these limits at the provider/API layer; a generic Python wrapper cannot forcibly stop an arbitrary blocking function. The adapter independently checks input and output character limits.

There is one invocation and no automatic retry. A provider exception is converted into a generic error so prompt content is not repeated in exception messages. Invalid output is discarded.

## Trust and privacy boundaries

- The caller, not the model, supplies the source event ID and allowed evidence identifiers.
- The model receives only the selected evidence fragments, not a full chat transcript or memory database.
- Evidence text is explicitly labelled untrusted data. Prompt-injection attempts inside evidence must not be followed.
- The injected transport must provide plain text generation only, with tools/function calling disabled.
- The returned proposal is not persisted and does not change any internal state.
- Evidence-reference membership proves only that an ID was supplied, not that its content supports the claim.
- The caller is responsible for choosing an approved local/private model endpoint and obtaining any consent required for transient analysis.

## Provider integration boundary

A provider shim can implement the callable interface:
`generate(prompt, max_output_tokens, timeout_seconds) -> str`.

The Emotion Engine does not import Hermes or a specific inference client. A later integration phase can bind the callable to Hermes/Gemma after validating the installed Hermes version and testing in an isolated profile. No active WhatsApp profile is changed by this phase.

## Verification

Run:

```bash
python -m unittest discover -s tests -v
```

Tests use a fake generator. They verify one-shot invocation, prompt minimisation, budget propagation, rejection of invalid outputs, and fail-closed behavior. They do not demonstrate live Gemma compatibility.
