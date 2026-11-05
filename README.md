# CloudLinks Assistant

A conversational assistant built on OpenAI function calling. It answers questions from a local knowledge table and manages meetings (schedule, list, cancel) through natural-language chat, from either a command line or a web interface.

## Features

- Information lookup (`get_info`) backed by a local SQLite table
- Meeting management (`schedule_meeting`, `list_meetings`, `cancel_meeting`) stored in the same database
- Tool-calling loop capped at four iterations per turn
- Two interfaces: a CLI and a Next.js chat app

## Tech stack

- **Backend:** Python, OpenAI Chat Completions with function calling, FastAPI, SQLite
- **Frontend:** Next.js and TypeScript

## Interfaces

- **CLI** (`backend/main.py`): talks to the `Assistant` class directly.
- **Web UI** (`frontend/`): a Next.js chat app that talks to a small FastAPI wrapper (`backend/api.py`) around the same `Assistant` class.

## Setup

**Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # on Windows
# source venv/bin/activate   # on macOS/Linux
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your key:

```bash
copy .env.example .env
```

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

**Frontend** (only needed for the web UI)
```bash
cd frontend
npm install
```

## Run

**CLI**
```bash
cd backend
python main.py
```

On startup this creates `data/info.db` if it doesn't exist yet (two sample
`info` rows are seeded so there's something for `get_info` to find on a fresh
DB). Type `exit` or `quit` to stop.

**Web UI**

Start the backend API first, then the frontend, in two terminals:
```bash
cd backend
python -m uvicorn api:app --port 8000
```
```bash
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000). The frontend reads the
API's address from `frontend/.env.local` (`NEXT_PUBLIC_API_URL`, defaults to
`http://localhost:8000`).

## Adding info rows for testing

The `info` table is empty of anything beyond the two seed rows — load your
own reference data either with raw SQL:

```bash
cd backend
python -c "
import db
db.init_db()
db.insert_info('hr', 'Vacation requests need 2 weeks notice.')
"
```

or with `sqlite3` directly against `data/info.db`:

```sql
INSERT INTO info (category, content) VALUES ('billing', 'Invoices are sent on the 1st of each month.');
```

`get_info` does a `LIKE '%query%'` match against `content`, so keep entries
short and keyword-rich.

## Example conversations

**Info lookup**
```
You: what are our support hours?
[calling get_info...]
Bot: Based on what I have stored: Monday-Friday, 9am-6pm Beirut time.
```

**Scheduling** (the assistant may ask you to confirm ambiguous details, e.g.
a generated title, before booking)
```
You: schedule a meeting with Karim and Sara tomorrow at 3pm for 45 minutes about the Esolar project
Bot: I'll schedule "Esolar Project Meeting" for 2026-07-29 15:00-15:45 with Karim and Sara. Confirm?
You: yes go ahead
[calling schedule_meeting...]
Bot: Done! Scheduled "Esolar Project Meeting" for 2026-07-29 15:00-15:45 with Karim and Sara. (Meeting ID: 1)
```

**Checking meetings**
```
You: what meetings do I have this week?
[calling list_meetings...]
Bot: You have 1 meeting this week: Esolar Project Meeting, Jul 29, 3:00-3:45 PM, with Karim and Sara.
```

**Cancelling a meeting**
```
You: cancel my meeting with Karim and Sara
[calling list_meetings...]
[calling cancel_meeting...]
Bot: Done — "Esolar Project Meeting" (Jul 29, 3:00-3:45 PM) has been cancelled.
```
`cancel_meeting` looks up the meeting by id and sets its `status` to
`cancelled`; cancelled meetings are excluded from `list_meetings` results.
If the assistant doesn't already know the id from context, it calls
`list_meetings` first to find it.

## Architecture

```
backend/
    main.py        - CLI REPL loop
    api.py         - FastAPI wrapper (POST /chat) exposing the Assistant over HTTP, for the frontend
    assistant.py   - message history, OpenAI chat completions call, tool-call loop (capped at 4 iterations/turn)
    tools.py       - get_info / schedule_meeting / list_meetings / cancel_meeting + their JSON schemas
    db.py          - sqlite3 access layer (info + meetings tables)
    data/info.db   - generated SQLite file (gitignored)

frontend/
    app/                     - pages (layout, home page, global styles)
    components/              - chat window, message bubble, input bar, typing indicator
    lib/api.ts               - the only file that calls the backend (POST /chat)
    types.ts                 - shared Message type
```

## Scope / future improvements (not built)

- No auth — CLI and web UI are both single-user, local-only.
- No "learn from chat" logic — `info` is populated manually, not from conversation.
- No timezone-aware storage — timestamps are naive ISO 8601, resolved by the
  model against the local system clock at each turn. Fine for a single-user
  local tool; would need explicit timezone handling for multi-user/remote use.
- No conflict detection between overlapping meetings (out of scope; could be
  added to `schedule_meeting` if double-booking becomes a concern).
- `cancel_meeting` only sets status to `cancelled`; there's no "completed" or
  reschedule/update tool yet, though the `status` column supports it.
- No conversation persistence in the web UI — chat history lives in browser
  memory and resets on page reload. The backend's `Assistant` instance keeps
  history for the life of the server process, shared across anyone hitting
  the API.
