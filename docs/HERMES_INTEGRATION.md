# Hermes Integration

**Status:** native plugin implementation is under active development. It
targets Hermes Agent v0.23.1's documented native plugin API. It has not been
installed or enabled in a live profile.

## Plugin boundary

The repository root contains a native `plugin.yaml` and `register(ctx)`
entry point. The adapter uses documented public plugin surfaces:
`ctx.register_tool()`, `ctx.register_hook("post_llm_call")`,
`ctx.register_auxiliary_task()`, and `ctx.llm.complete()`.

No Hermes private modules, monkeypatches, tool overrides, platform actions, or
privileged capabilities are requested.

## What the plugin does

1. After a successful assistant turn, the hook stores only the final
   `assistant_response` in a bounded, per-session in-memory cache.
2. It deliberately ignores `user_message` and `conversation_history`.
3. The model can call `emotion_list_recent_actions` to select a response.
4. `emotion_reflect` sends that response plus explicitly supplied evidence
   to the standalone `SelfObservationEngine`. The engine performs exactly
   one `ctx.llm.complete()` call through the registered auxiliary task.
5. If a concrete follow-up question is produced,
   `emotion_continue_reflection` can advance the cascade once after genuinely
   new evidence is supplied.
6. `emotion_clear_session` clears the current session's volatile response
   and cascade cache.

The cache is bounded to 24 sessions, 32 responses per session, and 8 cascades
per session. Responses are truncated to 2,000 characters. Process restart
clears all captured data. Nothing is written to SQLite or the filesystem by
the Hermes adapter.

## Optional KIE publication

When KIE is installed in the same Python environment and `kie_database` is
configured as an absolute path, the plugin publishes one
`emotion.reflection_summary` event after each successful explicit
`emotion_reflect` or `emotion_continue_reflection` call.

Only reflection status, step counts, assessment labels, and aggregate
evidence/hypothesis counts are transferred. The KIE event excludes captured
assistant response text, findings, self-challenges, causal-hypothesis text,
next-question text, evidence content, emotion labels, and persistent
emotional-memory records. It does not change the Emotion Engine's volatile
cascade state.

Publication is optional and fail-open. A missing KIE package, relative path,
or database error cannot block a reflection result. The KIE event is marked
as a hypothesis, never as verified.

Example plugin settings:

```yaml
plugins:
  entries:
    emotion-engine:
      settings:
        kie_database: /absolute/path/to/kie-integration.sqlite3
```

The KIE event ledger remains owned by KIE. Protect the database using host
filesystem permissions.

## Privacy and evidence boundaries

- The plugin does not expose the Emotion Engine's persistent emotional-memory
  APIs. No emotional memory is stored by this integration.
- The captured final assistant response may contain sensitive content; it
  remains in process memory only and is isolated by Hermes `session_id`.
- The reflection prompt contains the captured assistant response and only
  evidence explicitly supplied to the reflection tool.
- Evidence source labels are caller-declared; the plugin cannot independently
  authenticate a model-supplied claim that a fragment came from a tool or
  system log.
- No hidden chain-of-thought, model weights, activations, or concealed intent
  are captured or inspected.
- A contradiction is not proof of deliberate lying. Findings and causal
  explanations remain model-generated proposals.

## Registered tools

| Tool | Purpose |
|---|---|
| `emotion_list_recent_actions` | List recent assistant responses in this active session |
| `emotion_reflect` | Start one evidence-grounded audit of a selected response |
| `emotion_continue_reflection` | Advance one step with new evidence |
| `emotion_clear_session` | Clear volatile cache for the active session |

## Resource limits

- One model invocation per explicit start/continue tool call.
- Maximum four reflection steps per cascade.
- Maximum 1,000 requested output tokens and 45-second requested timeout per
  step.
- No plugin-level retry, recursive call, background job, automatic
  reflection, or persistent memory write.
- The auxiliary task can be pinned to a separate model in Hermes
  configuration without the plugin choosing a provider or model itself.

## Installation and isolated validation

After this PR is merged, run these commands in an isolated Hermes profile:

1. `hermes plugins validate /path/to/Emotion-Engine`
2. `hermes plugins doctor /path/to/Emotion-Engine`
3. `hermes plugins install oORaxaOo/Emotion-Engine --ref MERGED_COMMIT_SHA`
4. `hermes plugins enable emotion-engine`

Do not enable the plugin in the live WhatsApp profile until the doctor check
and a local-model smoke test pass.

## What remains unverified

GitHub CI can test the plugin's registration contract and handlers with a
fake Hermes context and fake LLM response. It cannot prove the real v0.23.1
plugin loader, profile routing, local model response quality, or WhatsApp
gateway behavior. Those require isolated checks and a controlled smoke test.
Persistent-memory APIs remain intentionally disconnected until a secure key
provider and real consent interface exist.
