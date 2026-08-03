export function readCodexTurnMetadata() {
  const metadata = nodeRepl.requestMeta?.["x-codex-turn-metadata"];
  if (!metadata || typeof metadata !== "object") {
    throw new Error("x-codex-turn-metadata is unavailable in this root tool call");
  }
  if (metadata.thread_source !== "user") {
    throw new Error(
      `root user turn metadata required; received thread_source=${metadata.thread_source}`,
    );
  }
  if (typeof metadata.turn_id !== "string" || metadata.turn_id.length === 0) {
    throw new Error("Codex turn metadata has no turn_id");
  }
  if (
    !Number.isSafeInteger(metadata.turn_started_at_unix_ms) ||
    metadata.turn_started_at_unix_ms < 0
  ) {
    throw new Error("Codex turn metadata has no millisecond request timestamp");
  }
  return {
    turn_id: metadata.turn_id,
    turn_started_at_unix_ms: metadata.turn_started_at_unix_ms,
    thread_id: metadata.thread_id ?? null,
    session_id: metadata.session_id ?? null,
    source: "codex-request-metadata",
    precision_ms: 1,
  };
}
