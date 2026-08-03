from dateutil import parser as dateutil_parser

import db


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

    return db.insert_meeting(title, start_time, end_time, participants, notes)


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
