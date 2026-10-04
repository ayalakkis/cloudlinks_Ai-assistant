import json
import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
from pprint import pprint

from tools import TOOLS, TOOL_IMPLEMENTATIONS

load_dotenv()

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOOL_ITERATIONS = 4

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _system_prompt() -> str:
    now = datetime.now()
    return (
        "You are a personal assistant. You have three kinds of tools: `get_info` for "
        "short internal notes (support hours, team info, to-do lists) -- NOT for offers, "
        "discounts, or anything that sounds like it came from an uploaded file; "
        "`search_documents` for anything about uploaded PDF/TXT documents, including "
        "offers, discounts, promotions, or pricing -- when in doubt about where an answer "
        "lives, try `search_documents` first, and answer using only the chunks it "
        "returns, with no outside knowledge mixed in, even as a bonus or aside; if it "
        "returns no chunks, just say you don't have enough information from the "
        "uploaded documents and stop there; and meeting tools -- `schedule_meeting`, "
        "`list_meetings`, `cancel_meeting` (given an id from `list_meetings`). Always "
        "confirm meeting details with the user if anything is ambiguous before "
        "scheduling or cancelling.\n\n"
        f"The current date and time is {now.isoformat(timespec='seconds')} "
        f"({now.strftime('%A')}). Resolve any relative dates or times the user gives "
        "(e.g. 'tomorrow', 'next Monday at 2pm') against this, and pass fully-qualified "
        "ISO 8601 datetimes to tools."
    )


class Assistant:
    def __init__(self):
        self.messages = [{"role": "system", "content": _system_prompt()}]

    def send(self, user_message: str, on_tool_call=None) -> str:
        self.messages.append({"role": "user", "content": user_message})

        for i in range(MAX_TOOL_ITERATIONS):
            pprint(f"ITERATION Number: {i + 1}")

            pprint("SENDING TO OPENAI:")
            pprint(self.messages)
            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS,
            )

            pprint("RECEIVED FROM OPENAI:")

            pprint (response)

            message = response.choices[0].message

            if not message.tool_calls:
                self.messages.append({"role": "assistant", "content": message.content})
                return message.content

            self.messages.append(message.model_dump(exclude_unset=True))

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                if on_tool_call:
                    on_tool_call(name)
                try:
                    args = json.loads(tool_call.function.arguments)
                    func = TOOL_IMPLEMENTATIONS[name]
                    result = func(**args)
                except Exception as exc:
                    result = {"error": f"tool '{name}' failed: {exc}"}

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    }
                )

        fallback = (
            "I wasn't able to finish that after several tool calls — "
            "could you clarify what you'd like me to do?"
        )
        self.messages.append({"role": "assistant", "content": fallback})
        return fallback
