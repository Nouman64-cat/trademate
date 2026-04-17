"use client";

import { useCallback, useRef, useState } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

export type VoiceStatus = "idle" | "connecting" | "active" | "ended";

export interface VoiceState {
  status: VoiceStatus;
  /** Transcript text accumulated so far (assistant turns + user transcriptions). */
  transcript: string;
  elapsedSeconds: number;
  error: string | null;
  /** Non-null while a tool call is in progress — shown in the modal UI. */
  toolActivity: string | null;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const SESSION_LIMIT_SECONDS = 60;

// ── Audio helpers ─────────────────────────────────────────────────────────────

/** Decode a base64-encoded PCM16 payload to Float32 samples. */
function pcm16Base64ToFloat32(base64: string): Float32Array {
  const raw = atob(base64);
  const bytes = Uint8Array.from({ length: raw.length }, (_, i) =>
    raw.charCodeAt(i)
  );
  const pcm16 = new Int16Array(bytes.buffer);
  const f32 = new Float32Array(pcm16.length);
  for (let i = 0; i < pcm16.length; i++) f32[i] = pcm16[i] / 32768;
  return f32;
}

/** Encode Float32 samples as a base64-encoded PCM16 payload. */
function float32ToPcm16Base64(f32: Float32Array): string {
  const pcm16 = new Int16Array(f32.length);
  for (let i = 0; i < f32.length; i++) {
    const clamped = Math.max(-1, Math.min(1, f32[i]));
    pcm16[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
  }
  const bytes = new Uint8Array(pcm16.buffer);
  let bin = "";
  for (let i = 0; i < bytes.byteLength; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

// ── Hook ──────────────────────────────────────────────────────────────────────

/**
 * Manages a single 60-second voice session with the TradeMate backend.
 *
 * Flow:
 *   1. start() → request mic → open WS to /v1/voice/stream → configure
 *      OpenAI Realtime session → stream PCM16 mic audio
 *   2. Incoming audio deltas are played back immediately via AudioContext.
 *   3. After 60 s (or on stop()) everything is torn down.
 */
export function useVoice(token: string) {
  const [state, setState] = useState<VoiceState>({
    status: "idle",
    transcript: "",
    elapsedSeconds: 0,
    error: null,
    toolActivity: null,
  });

  // Stable refs so callbacks never have stale closures
  const statusRef = useRef<VoiceStatus>("idle");
  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  // ScriptProcessorNode is deprecated but has widest browser support without
  // a separate AudioWorklet file.
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Monotonically-advancing playback cursor so audio chunks don't overlap.
  const playbackCursorRef = useRef<number>(0);
  // All currently scheduled/playing AudioBufferSourceNodes — needed for barge-in.
  const activeSourcesRef = useRef<AudioBufferSourceNode[]>([]);

  // ── Cleanup ──────────────────────────────────────────────────────────────

  const cleanup = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    playbackCursorRef.current = 0;
    activeSourcesRef.current = [];
  }, []);

  // ── Stop ─────────────────────────────────────────────────────────────────

  const stop = useCallback(
    (reason: "user" | "timeout" | "error" = "user") => {
      if (statusRef.current === "ended") return;
      statusRef.current = "ended";
      cleanup();
      setState((s) => ({
        ...s,
        status: "ended",
        toolActivity: null,
        error:
          reason === "error"
            ? "Connection lost. Please try again."
            : null,
      }));
    },
    [cleanup]
  );

  // ── Start ─────────────────────────────────────────────────────────────────

  const start = useCallback(async () => {
    if (statusRef.current !== "idle" && statusRef.current !== "ended") return;
    statusRef.current = "connecting";
    setState({ status: "connecting", transcript: "", elapsedSeconds: 0, error: null });

    // Request microphone access
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
      });
    } catch {
      statusRef.current = "idle";
      setState((s) => ({
        ...s,
        status: "idle",
        error: "Microphone access denied. Please allow microphone access and try again.",
      }));
      return;
    }
    streamRef.current = stream;

    // AudioContext at 24 kHz — required by OpenAI Realtime API
    const audioCtx = new AudioContext({ sampleRate: 24000 });
    audioCtxRef.current = audioCtx;
    playbackCursorRef.current = audioCtx.currentTime;

    // WebSocket URL: swap http(s) → ws(s)
    const serverUrl =
      process.env.NEXT_PUBLIC_SERVER_URL ?? "http://localhost:8000";
    const wsBase = serverUrl.replace(/^http/, "ws");
    const ws = new WebSocket(
      `${wsBase}/v1/voice/stream?token=${encodeURIComponent(token)}`
    );
    wsRef.current = ws;

    ws.onopen = () => {
      // Guard: if cleanup already ran and replaced / nulled the ref, this is a
      // zombie connection — close it immediately and bail out.
      if (wsRef.current !== ws) {
        ws.close();
        return;
      }
      statusRef.current = "active";
      setState((s) => ({ ...s, status: "active" }));

      // NOTE: session.update (incl. tool definitions) is sent by the server
      // in voice.py right after connecting to OpenAI. No client config needed.

      // 60-second countdown
      let elapsed = 0;
      timerRef.current = setInterval(() => {
        elapsed += 1;
        setState((s) => ({ ...s, elapsedSeconds: elapsed }));
        if (elapsed >= SESSION_LIMIT_SECONDS) stop("timeout");
      }, 1000);

      // Stream microphone audio to the server
      const micSource = audioCtx.createMediaStreamSource(stream);
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      processor.onaudioprocess = (ev) => {
        if (ws.readyState !== WebSocket.OPEN) return;
        const samples = ev.inputBuffer.getChannelData(0);
        ws.send(
          JSON.stringify({
            type: "input_audio_buffer.append",
            audio: float32ToPcm16Base64(samples),
          })
        );
      };
      micSource.connect(processor);
      // Connect to destination to keep the graph alive (no audible output from mic)
      processor.connect(audioCtx.destination);
    };

    ws.onmessage = (ev) => {
      // Ignore messages from superseded connections
      if (wsRef.current !== ws) return;
      let event: Record<string, unknown>;
      try {
        event = JSON.parse(ev.data as string);
      } catch {
        return;
      }

      // Play assistant audio chunks in order
      if (event.type === "response.audio.delta" && typeof event.delta === "string") {
        const f32 = pcm16Base64ToFloat32(event.delta);
        const buffer = audioCtx.createBuffer(1, f32.length, 24000);
        buffer.copyToChannel(f32, 0);
        const source = audioCtx.createBufferSource();
        source.buffer = buffer;
        source.connect(audioCtx.destination);
        // Schedule chunk sequentially to prevent overlap/gaps
        const startAt = Math.max(playbackCursorRef.current, audioCtx.currentTime);
        source.start(startAt);
        playbackCursorRef.current = startAt + buffer.duration;
        activeSourcesRef.current.push(source);
        source.onended = () => {
          activeSourcesRef.current = activeSourcesRef.current.filter((s) => s !== source);
        };
      }

      // Tool call started — show activity label in modal
      if (
        event.type === "response.output_item.added" &&
        typeof event.item === "object" &&
        (event.item as Record<string, unknown>)?.type === "function_call"
      ) {
        const toolName = (event.item as Record<string, unknown>).name as string;
        const labels: Record<string, string> = {
          search_pakistan_hs_data: "Searching Pakistan tariff database…",
          search_us_hs_data: "Searching US HTS database…",
          search_trade_documents: "Searching trade documents…",
          evaluate_shipping_routes: "Evaluating shipping routes…",
        };
        setState((s) => ({
          ...s,
          toolActivity: labels[toolName] ?? "Looking up data…",
        }));
      }

      // Tool call finished — clear activity label when audio response begins
      if (event.type === "response.audio.delta") {
        setState((s) => (s.toolActivity ? { ...s, toolActivity: null } : s));
      }

      // Barge-in: user started speaking — stop all queued/playing AI audio immediately
      if (event.type === "input_audio_buffer.speech_started") {
        activeSourcesRef.current.forEach((s) => { try { s.stop(); } catch { /* already ended */ } });
        activeSourcesRef.current = [];
        playbackCursorRef.current = audioCtx.currentTime;
      }

      // Accumulate assistant transcript delta (streamed character by character)
      if (
        event.type === "response.audio_transcript.delta" &&
        typeof event.delta === "string"
      ) {
        setState((s) => ({ ...s, transcript: s.transcript + event.delta }));
      }

      // User speech transcription — append as a new labelled turn
      if (
        event.type ===
          "conversation.item.input_audio_transcription.completed" &&
        typeof event.transcript === "string" &&
        event.transcript.trim()
      ) {
        setState((s) => ({
          ...s,
          transcript:
            (s.transcript ? s.transcript + "\n\n" : "") +
            `You: ${event.transcript.trim()}`,
        }));
      }

      // Server-initiated session end (time limit or error)
      if (event.type === "session.ended") {
        stop("timeout");
      }
    };

    ws.onerror = () => {
      if (wsRef.current === ws && statusRef.current !== "ended") stop("error");
    };

    ws.onclose = () => {
      if (wsRef.current === ws && statusRef.current !== "ended") stop("user");
    };
  }, [token, stop]);

  return { state, start, stop };
}
