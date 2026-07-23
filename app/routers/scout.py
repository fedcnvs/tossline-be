"""Scout assistant: turn a coach's natural-language request into a structured
scout selection filter via OpenAI.

The LLM never sees the scout data and never returns action IDs — it only maps
language onto the filter fields below. The player applies that filter with its
own deterministic selection logic, so a bad/hallucinated response can never
invent a selection; the worst case is an empty or off-target filter, and the
player falls back to its local rule-based parser if this endpoint is
unreachable.

Gated behind get_current_user so it isn't an open OpenAI proxy on the public BE.
"""

import json
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.deps import get_current_user
from app.models import User

log = logging.getLogger(__name__)

router = APIRouter(prefix="/scout", tags=["scout"])

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class PlayerCtx(BaseModel):
    number: int
    lastName: str
    side: str  # "H" | "A"


class ScoutContext(BaseModel):
    homeCode: str
    awayCode: str
    sets: list[int] = []
    players: list[PlayerCtx] = []


class ScoutParseRequest(BaseModel):
    query: str
    context: ScoutContext


# Strict JSON schema for the filter. Every property is required and nullable
# where "not constrained" is meaningful; booleans default to false.
FILTER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "skill",
        "set",
        "side",
        "playerNumber",
        "wantsRallies",
        "wantsWon",
        "wantsLost",
        "wantsErrors",
        "wantsBest",
        "wantsPositive",
        "repeatAttacks",
    ],
    "properties": {
        "skill": {"type": ["string", "null"], "enum": ["S", "R", "A", "B", "D", "E", None]},
        "set": {"type": ["integer", "null"]},
        "side": {"type": ["string", "null"], "enum": ["H", "A", None]},
        "playerNumber": {"type": ["integer", "null"]},
        "wantsRallies": {"type": "boolean"},
        "wantsWon": {"type": "boolean"},
        "wantsLost": {"type": "boolean"},
        "wantsErrors": {"type": "boolean"},
        "wantsBest": {"type": "boolean"},
        "wantsPositive": {"type": "boolean"},
        "repeatAttacks": {"type": ["integer", "null"]},
    },
}

SYSTEM_PROMPT = """\
You convert a volleyball coach's natural-language request into a structured \
scout selection filter for a DataVolley match. Fill in only the fields the \
request actually constrains; leave everything else null (or false for booleans).

Field meanings:
- skill: the touch type. S=serve, R=reception, A=attack (spike/kill), B=block, \
D=defense/dig, E=set/setter. null if unspecified.
- side: "H"=home team, "A"=away/visiting team. Resolve team names or 3-letter \
codes to the correct side using the match context. null if unspecified.
- set: set number 1-5 if restricted to one set, else null.
- playerNumber: jersey number if the request names a player (resolve the name \
via the roster) or gives a number, else null.
- wantsRallies: true if the coach wants whole rallies rather than individual \
touches.
- wantsWon / wantsLost: true for rallies won / lost by the given side. Both \
require a side; if the coach says won/lost without naming a team, still set the \
flag and set side to null.
- wantsErrors: true for errors/mistakes.
- wantsBest: true for aces/kills/perfect/winning touches.
- wantsPositive: true for positive/good touches.
- repeatAttacks: N if the coach wants N attacks in a row by the same player in a \
rally (e.g. "twice in a row" -> 2, "three straight swings" -> 3), else null.

If the request is ambiguous about a field, leave it null/false rather than \
guessing.\
"""


def _build_user_content(payload: ScoutParseRequest) -> str:
    ctx = payload.context
    roster = "\n".join(
        f"  {p.side} #{p.number} {p.lastName}" for p in ctx.players
    ) or "  (roster unavailable)"
    sets = ", ".join(str(s) for s in ctx.sets) or "unknown"
    return (
        "Match context:\n"
        f"- Home team code: {ctx.homeCode} (side H)\n"
        f"- Away team code: {ctx.awayCode} (side A)\n"
        f"- Sets present: {sets}\n"
        f"- Roster:\n{roster}\n\n"
        f'Request: "{payload.query.strip()}"'
    )


@router.post("/parse")
async def parse_scout(
    payload: ScoutParseRequest,
    user: User = Depends(get_current_user),
) -> dict:
    if not settings.open_ai_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scout assistant is not configured.",
        )
    if not payload.query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empty query.",
        )

    body = {
        "model": settings.openai_model,
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "scout_filter",
                "strict": True,
                "schema": FILTER_SCHEMA,
            },
        },
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_content(payload)},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                OPENAI_URL,
                headers={"Authorization": f"Bearer {settings.open_ai_key}"},
                json=body,
            )
    except httpx.HTTPError as exc:
        log.warning("scout-parse upstream request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Scout assistant is temporarily unavailable.",
        )

    if resp.status_code != 200:
        log.warning("scout-parse upstream %s: %s", resp.status_code, resp.text[:500])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Scout assistant is temporarily unavailable.",
        )

    data = resp.json()
    message = data.get("choices", [{}])[0].get("message", {})
    if message.get("refusal"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not turn that into a scout selection.",
        )

    content = message.get("content")
    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Scout assistant returned no result.",
        )

    try:
        return json.loads(content)
    except (TypeError, ValueError):
        log.warning("scout-parse non-JSON content: %r", content[:500])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Scout assistant returned an invalid result.",
        )
