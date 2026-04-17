"""
routes/voice.py — WebSocket proxy to OpenAI Realtime API WITH tool execution.

WS /v1/voice/stream?token=<jwt>
───────────────────────────────
• Validates JWT from query param.
• Connects to OpenAI Realtime API using the server-side API key.
• Sends session.update from the server (not the client), so TradeMate's four
  tools are registered with the Realtime model.
• Intercepts response.output_item.done function-call events, runs the actual
  Python tool (Neo4j / Pinecone / route engine), sends the result back to
  OpenAI, then triggers a new response so the model speaks the answer.
• Bidirectionally proxies all other messages.
• Hard 60-second session limit.
"""

import asyncio
import json
import logging
import os
from typing import Any

import websockets
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from security.security import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["voice"])

_OPENAI_REALTIME_URL = (
    "wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview"
)
_SESSION_LIMIT_SECONDS = 60

# ── Tool schemas (OpenAI function-call format) ────────────────────────────────
# These mirror the LangChain tool definitions in agent/bot.py exactly.

_TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "name": "search_pakistan_hs_data",
        "description": (
            "Search Pakistan's PCT (Pakistan Customs Tariff) HS code database. "
            "Use for: Pakistan import/export tariffs, CD/RD/ACD/FED/ST rates, "
            "provincial cess, SRO exemptions, customs procedures, NTMs, and any "
            "product classified under Pakistan's PCT system."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Product name, 12-digit Pakistan HS code, or natural-language "
                        "description. Example: 'mobile phones', '851712000000'."
                    ),
                }
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "search_us_hs_data",
        "description": (
            "Search the US Harmonized Tariff Schedule (HTS) database. "
            "Use for: US import duty rates, US HTS codes, US trade classifications, "
            "General/Special/Column-2 rates, unit of quantity for US declarations."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Product name, US HTS code (e.g. '0101.21.00'), or "
                        "natural-language description."
                    ),
                }
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "search_trade_documents",
        "description": (
            "Search uploaded trade policy documents, regulations, and reports stored "
            "in Pinecone. Use for: trade policies, FTAs, WTO rules, SRO documents, "
            "compliance requirements, or any question needing policy/document context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural-language question. Example: "
                        "'SRO exemptions for textile', 'WTO safeguard measures'."
                    ),
                }
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "evaluate_shipping_routes",
        "description": (
            "Evaluate all viable shipping routes from a Pakistan city to a USA city. "
            "Use for: freight costs, transit times, ocean/air freight rates, "
            "comparing FCL/LCL/Air options, total landed cost estimates."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "origin_city": {
                    "type": "string",
                    "description": "Origin city in Pakistan (e.g. Karachi, Lahore, Faisalabad).",
                },
                "destination_city": {
                    "type": "string",
                    "description": "Destination city in the USA (e.g. Los Angeles, New York, Chicago).",
                },
                "cargo_type": {
                    "type": "string",
                    "enum": ["FCL_20", "FCL_40", "FCL_40HC", "LCL", "AIR"],
                    "description": "Shipping mode / container type.",
                },
                "cargo_value_usd": {
                    "type": "number",
                    "description": "Total declared cargo value in USD.",
                },
                "hs_code": {
                    "type": "string",
                    "description": "HS code (first 2–6 digits) for import duty calculation. Optional.",
                },
                "cargo_volume_cbm": {
                    "type": "number",
                    "description": "Cargo volume in CBM — required for LCL shipments.",
                },
                "cargo_weight_kg": {
                    "type": "number",
                    "description": "Cargo weight in kg — required for AIR shipments.",
                },
                "cost_weight": {
                    "type": "number",
                    "description": "Optimisation preference: 0 = fastest, 1 = cheapest, 0.5 = balanced.",
                },
            },
            "required": ["origin_city", "destination_city", "cargo_type", "cargo_value_usd"],
        },
    },
]

# ── Session configuration sent by the server ─────────────────────────────────

_SESSION_CONFIG = {
    "type": "session.update",
    "session": {
        "modalities": ["text", "audio"],
        "instructions": (
            "You are TradeMate, an expert AI assistant specialising in international "
            "trade, HS codes, import/export regulations, tariff schedules, and "
            "Pakistan-to-USA shipping logistics. "
            "ALWAYS call at least one tool for every trade-related question — "
            "never answer from training knowledge alone. "
            "Keep spoken replies concise and clear — the user is listening, not reading. "
            "When you call evaluate_shipping_routes, summarise the result briefly "
            "(2–3 sentences) mentioning the cheapest option and fastest transit time."
        ),
        "voice": "alloy",
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "input_audio_transcription": {"model": "whisper-1"},
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.5,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 500,
        },
        "tools": _TOOL_SCHEMAS,
        "tool_choice": "auto",
    },
}


# ── Tool execution ────────────────────────────────────────────────────────────


async def _execute_tool(name: str, args_str: str) -> str:
    """
    Look up `name` in the agent's tool registry and invoke it in a thread pool
    (all tools are synchronous — Neo4j/Pinecone calls are blocking).
    """
    from agent.bot import _TOOL_MAP  # import here to avoid circular imports at load time

    tool_fn = _TOOL_MAP.get(name)
    if tool_fn is None:
        logger.warning("━━━ [VOICE TOOL] Unknown tool requested: %s", name)
        return f"Tool '{name}' is not available."

    try:
        args: dict[str, Any] = json.loads(args_str) if args_str else {}
    except json.JSONDecodeError:
        return f"Could not parse tool arguments: {args_str}"

    logger.info("━━━ [VOICE TOOL] Calling %s  args=%s", name, str(args)[:200])
    try:
        result: str = await asyncio.to_thread(tool_fn.invoke, args)
        logger.info("━━━ [VOICE TOOL] %s returned %d chars", name, len(result))
        return result
    except Exception as exc:  # noqa: BLE001
        logger.exception("━━━ [VOICE TOOL] %s failed: %s", name, exc)
        return f"Tool execution failed: {exc}"


# ── WebSocket endpoint ────────────────────────────────────────────────────────


@router.websocket("/voice/stream")
async def voice_stream(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """Proxy WebSocket messages between the browser and OpenAI Realtime API."""

    # ── Authentication ────────────────────────────────────────────────────────
    try:
        payload = decode_access_token(token)
        user_id = int(payload["id"])
    except Exception:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    logger.info("━━━ [VOICE] Session started  user_id=%d", user_id)

    api_key = os.getenv("OPENAI_API_KEY", "")

    try:
        async with websockets.connect(
            _OPENAI_REALTIME_URL,
            additional_headers={
                "Authorization": f"Bearer {api_key}",
                "OpenAI-Beta": "realtime=v1",
            },
        ) as openai_ws:

            # Send server-controlled session config (includes tool definitions)
            await openai_ws.send(json.dumps(_SESSION_CONFIG))
            logger.info("━━━ [VOICE] Session config sent (tools registered)")

            # ── Client → OpenAI ───────────────────────────────────────────────

            async def client_to_openai() -> None:
                """Forward client messages to OpenAI, skipping session.update
                (server owns configuration so tools are never overwritten)."""
                try:
                    while True:
                        data = await websocket.receive_text()
                        try:
                            parsed = json.loads(data)
                            if parsed.get("type") == "session.update":
                                # Server already sent a full session.update with tools;
                                # ignore client-side one to prevent tool list being wiped.
                                continue
                        except json.JSONDecodeError:
                            pass
                        await openai_ws.send(data)
                except (WebSocketDisconnect, websockets.ConnectionClosed):
                    pass

            # ── OpenAI → Client (with tool execution) ────────────────────────

            async def openai_to_client() -> None:
                """Forward OpenAI messages to client.  Intercept function-call
                completions, execute the tool, and return the result to OpenAI."""
                try:
                    async for message in openai_ws:
                        text = (
                            message if isinstance(message, str) else message.decode()
                        )

                        # ── Tool call interception ────────────────────────────
                        try:
                            event = json.loads(text)
                        except json.JSONDecodeError:
                            event = {}

                        if (
                            event.get("type") == "response.output_item.done"
                            and isinstance(event.get("item"), dict)
                            and event["item"].get("type") == "function_call"
                        ):
                            item = event["item"]
                            fn_name  = item.get("name", "")
                            fn_args  = item.get("arguments", "{}")
                            call_id  = item.get("call_id", "")

                            result = await _execute_tool(fn_name, fn_args)

                            # Return tool output to OpenAI
                            await openai_ws.send(json.dumps({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_id,
                                    "output": result,
                                },
                            }))
                            # Ask OpenAI to continue the response (speak the answer)
                            await openai_ws.send(json.dumps({"type": "response.create"}))

                        # Forward every event to the client regardless
                        try:
                            await websocket.send_text(text)
                        except (WebSocketDisconnect, RuntimeError):
                            return

                except websockets.ConnectionClosed:
                    pass

            # ── Run with hard 60-second time limit ───────────────────────────
            try:
                await asyncio.wait_for(
                    asyncio.gather(client_to_openai(), openai_to_client()),
                    timeout=_SESSION_LIMIT_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.info(
                    "━━━ [VOICE] 60-second limit reached  user_id=%d", user_id
                )
                try:
                    await websocket.send_text(
                        json.dumps(
                            {"type": "session.ended", "reason": "time_limit"}
                        )
                    )
                except Exception:
                    pass

    except Exception:
        logger.exception("━━━ [VOICE] Unexpected error  user_id=%d", user_id)
    finally:
        logger.info("━━━ [VOICE] Session ended  user_id=%d", user_id)
        try:
            await websocket.close()
        except Exception:
            pass
