import base64
import json
import os
import urllib.error
import urllib.request

from dateutil import parser as dateutil_parser

import db


def _notify_meeting_confirmed(meeting: dict) -> bool:
    """POSTs the confirmed meeting to the automation webhook (if one is configured
    in .env), using HTTP Basic Auth. Returns True/False for success; never raises,
    so a webhook outage can never block a meeting from being saved."""
    # Read the webhook settings fresh on each call (not at import time), since this
    # module can be imported before .env has been loaded by assistant.py.
    webhook_url = os.environ.get("MEETING_WEBHOOK_URL")
    if not webhook_url:
        return False

    body = json.dumps(meeting).encode("utf-8")  # the meeting record, sent as JSON
    request = urllib.request.Request(webhook_url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    # Cloudflare (in front of the webhook) blocks Python's default User-Agent as a
    # bot signature (HTTP 403, Cloudflare error 1010) -- a normal-looking one passes.
    request.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AssistantBot/1.0")

    username = os.environ.get("MEETING_WEBHOOK_USERNAME")
    password = os.environ.get("MEETING_WEBHOOK_PASSWORD")
    if username:
        # Basic Auth header = base64("username:password")
        creds = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        request.add_header("Authorization", f"Basic {creds}")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"[warning] meeting confirmation webhook failed: {exc}")
        return False


def get_info(query: str) -> list[str]:
    """Keyword search over the info table. Empty list if nothing matches or the table is empty."""
    return db.get_info_entries(query)


def schedule_meeting(
    title: str,
    start_time: str,
    end_time: str,
    participants: list[str],
    notes: str = "",
) -> dict:
    """Validates inputs and inserts a meeting record. Returns the created record or {"error": ...}."""
    if not title or not isinstance(title, str):
        return {"error": "title is required"}

    if not participants or not isinstance(participants, list) or not all(
        isinstance(p, str) for p in participants
    ):
        return {"error": "participants must be a non-empty list of strings"}

    try:
        start_dt = dateutil_parser.isoparse(start_time)
        end_dt = dateutil_parser.isoparse(end_time)
    except (ValueError, TypeError):
        return {"error": "start_time and end_time must be valid ISO 8601 strings"}

    if end_dt <= start_dt:
        return {"error": "end_time must be after start_time"}

    record = db.insert_meeting(title, start_time, end_time, participants, notes)
    # Notify the automation webhook now that the meeting is actually confirmed/saved.
    record["confirmation_sent"] = _notify_meeting_confirmed(record)
    return record


def list_meetings(from_date: str = None, to_date: str = None) -> list[dict]:
    """Returns meetings, optionally filtered to an ISO date/datetime range."""
    return db.list_meetings(from_date=from_date, to_date=to_date)


def cancel_meeting(meeting_id: int) -> dict:
    """Cancels a scheduled meeting by id. Returns the updated record or {"error": ...}."""
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        return {"error": f"no meeting found with id {meeting_id}"}
    if meeting["status"] == "cancelled":
        return {"error": f"meeting {meeting_id} is already cancelled"}

    return db.set_meeting_status(meeting_id, "cancelled")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_info",
            "description": (
                "Search stored reference/knowledge info by keyword — e.g. support hours, "
                "policies, pricing, team info, and to-do/priority items (including weekly "
                "and monthly to-do lists). Returns a list of matching text snippets, or an "
                "empty list if nothing is stored or nothing matches."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keyword or phrase to search for.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": (
                "Schedule a meeting and save it to the database. start_time and end_time "
                "must be ISO 8601 datetime strings (convert any natural-language time "
                "before calling this)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Meeting title/subject."},
                    "start_time": {
                        "type": "string",
                        "description": "ISO 8601 datetime, e.g. 2026-07-29T15:00:00",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "ISO 8601 datetime, e.g. 2026-07-29T15:45:00",
                    },
                    "participants": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Names of meeting participants.",
                    },
                    "notes": {"type": "string", "default": ""},
                },
                "required": ["title", "start_time", "end_time", "participants"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_meetings",
            "description": "List scheduled meetings, optionally filtered by an ISO date/datetime range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_date": {
                        "type": "string",
                        "description": "ISO 8601 date/datetime lower bound (inclusive), optional.",
                    },
                    "to_date": {
                        "type": "string",
                        "description": "ISO 8601 date/datetime upper bound (inclusive), optional.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_meeting",
            "description": (
                "Cancel a previously scheduled meeting by its id (sets status to "
                "'cancelled'). Use list_meetings first if you need to find the id."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "integer",
                        "description": "The id of the meeting to cancel.",
                    },
                },
                "required": ["meeting_id"],
            },
        },
    },
]

TOOL_IMPLEMENTATIONS = {
    "get_info": get_info,
    "schedule_meeting": schedule_meeting,
    "list_meetings": list_meetings,
    "cancel_meeting": cancel_meeting,
}
