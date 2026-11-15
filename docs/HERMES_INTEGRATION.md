# Hermes Integration

**Status:** native plugin implementation in review (Phase 8). It targets Hermes Agent v0.23.1's documented native plugin API. It has not been installed or enabled in a live profile.

## Plugin boundary

The repository root contains a native plugin.yaml and register(ctx) entry point. The adapter uses only documented public plugin surfaces: ctx.register_tool(), ctx.register_hook("post_llm_call"), ctx.register_auxiliary_task(), and ctx.llm.complete().

No Hermes private modules, monkeypatches, tool overrides, platform actions, or privileged capabilities are requested.

## What the plugin does

1. After a successful assistant turn, the hook stores only the final assistant_response in a bounded, per-session in-memory cache.
2. It deliberately ignores user_message and conversation_history.
3. The model can call emotion_list_recent_actions to select a response.
4. emotion_reflect sends that response plus explicitly supplied evidence to the standalone SelfObservationEngine. The engine performs exactly one ctx.llm.complete() call through the plugin's registered emotion_reflection auxiliary task.
5. If a concrete follow-up question is produced, the model can call emotion_continue_reflection once after obtaining genuinely new evidence. The core enforces the four-step cascade ceiling and rejects reused evidence.
6. emotion_clear_session clears the current session's volatile response and cascade cache.

The cache is bounded to 24 sessions, 32 responses per session, and 8 cascades per session. Responses are truncated to 2,000 characters. Process restart clears all captured data. Nothing is written to SQLite or the filesystem by the Hermes adapter.

## Privacy and evidence boundaries

- The plugin does not expose the Emotion Engine's persistent emotional-memory APIs. No emotional memory is stored by this integration.
- The captured final assistant response may contain sensitive content; it remains in process memory only and is isolated by Hermes session_id.
- The reflection prompt contains the captured assistant response and only the evidence explicitly supplied to the reflection tool. Hermes ctx.llm uses the configured provider/model route for the registered auxiliary task.
- By default, the auxiliary task follows the user's active Hermes model. If privacy requires local-only processing, configure auxiliary.emotion_reflection to a local/private endpoint before using reflection. The plugin itself cannot certify whether a configured endpoint is local.
- Evidence source labels are caller-declared. The plugin cannot independently authenticate a model-supplied claim that a fragment came from a tool or system log.
- No hidden chain-of-thought, model weights, activations, or concealed intent are captured or inspected.
- A contradiction is not proof of deliberate lying. Findings and causal explanations remain model-generated proposals.

## Registered tools

| Tool | Purpose |
|---|---|
| emotion_list_recent_actions | List recent assistant responses in this active session |
| emotion_reflect | Start one evidence-grounded audit of a selected response |
| emotion_continue_reflection | Advance exactly one step with new evidence |
| emotion_clear_session | Clear volatile cache for the active session |

## Resource limits

- One model invocation per explicit start/continue tool call.
- Maximum four reflection steps per cascade.
- Maximum 1,000 requested output tokens and 45-second requested timeout per step. Hermes/provider transport remains responsible for enforcing its own deadline.
- No plugin-level retry, recursive call, background job, automatic reflection, or persistent memory write.
- The auxiliary task can be pinned to a separate model in Hermes configuration without the plugin choosing a provider or model itself.

## Installation and isolated validation

After this PR is merged, run these commands in an isolated Hermes profile:

1. hermes plugins validate /path/to/Emotion-Engine
2. hermes plugins doctor /path/to/Emotion-Engine
3. hermes plugins install oORaxaOo/Emotion-Engine --ref MERGED_COMMIT_SHA
4. hermes plugins enable emotion-engine

Do not enable the plugin in the live WhatsApp profile until the doctor check and a local-model smoke test pass. Enabling the plugin is an explicit user action; this repository does not change Hermes configuration.

To route reflection to a local model, configure the registered task emotion_reflection under Hermes auxiliary model settings. The plugin follows that route and does not request provider/model override permissions.

## What remains unverified

GitHub CI can test the plugin's registration contract and handlers with a fake Hermes context and fake LLM response. It cannot prove the real v0.23.1 plugin loader, profile routing, local Gemma response quality, or WhatsApp gateway behavior. Those require hermes plugins validate, hermes plugins doctor, and a smoke test on the user's machine. Persistent-memory APIs remain intentionally disconnected until a secure key provider and real consent interface exist.
