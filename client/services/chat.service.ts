/**
 * chat.service.ts
 *
 * Handles the POST /v1/chat SSE stream.
 * Axios buffers responses, so we use native fetch here for streaming.
 */

import type { Message } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_SERVER_URL ?? "http://localhost:8000";

export type SSETokenEvent = { type: "token"; content: string; conversation_id: string };
export type SSEDoneEvent  = { type: "done";  conversation_id: string };
export type SSEErrorEvent = { type: "error"; detail: string; conversation_id: string };
export type SSEEvent = SSETokenEvent | SSEDoneEvent | SSEErrorEvent;

/**
 * Stream a chat response from the backend.
 *
 * @param message         The new user message.
 * @param conversationId  Frontend conversation ID (echoed back in SSE events).
 * @param history         Prior turns in this conversation (oldest first).
 * @param onChunk         Called with the *accumulated* assistant text on every token.
 * @param signal          Optional AbortSignal to cancel the stream.
 */
export async function streamChat(
  message: string,
  conversationId: string,
  history: Message[],
  onChunk: (accumulated: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const token = typeof window !== "undefined"
    ? localStorage.getItem("tm_access_token")
    : null;

  const response = await fetch(`${BASE_URL}/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      // Send history as role/content pairs (exclude the placeholder assistant message)
      history: history
        .filter((m) => m.role === "user" || (m.role === "assistant" && m.content !== ""))
        .map((m) => ({ role: m.role, content: m.content })),
    }),
    signal,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? `HTTP ${response.status}`);
  }

  const reader  = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) throw new Error("No response body");

  let accumulated = "";
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE lines are separated by \n\n
    const parts = buffer.split("\n\n");
    // The last element may be an incomplete chunk — keep it in the buffer
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;

      const json = line.slice("data:".length).trim();
      if (!json) continue;

      let event: SSEEvent;
      try {
        event = JSON.parse(json);
      } catch {
        continue;
      }

      if (event.type === "token") {
        accumulated += event.content;
        onChunk(accumulated);
      } else if (event.type === "error") {
        throw new Error(event.detail);
      }
      // "done" event — nothing to do, the while loop will exit naturally
    }
  }
}
