"""Core assistant logic: message history, OpenAI calls, and the tool-call loop."""

import json
import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOLS, TOOL_IMPLEMENTATIONS

load_dotenv()  # reads the .env file into the environment so os.environ[...] below can find it

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # which AI model to use; gpt-4o-mini if not set
MAX_TOOL_ITERATIONS = 4  # cap on how many tool round-trips a single message can trigger

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])  # reusable connection to the OpenAI API


def _system_prompt() -> str:
    """Builds the instruction message sent to the model, including today's live date
    so it can correctly resolve things like "tomorrow" or "next Monday"."""
    now = datetime.now()
    return (
        "You are a personal assistant. You can answer questions using the `get_info` "
        "tool when relevant, and schedule meetings using `schedule_meeting` (check "
        "existing ones with `list_meetings`, and cancel one with `cancel_meeting` given "
        "its id). Always confirm meeting details with the user if anything is ambiguous "
        "before scheduling or cancelling.\n\n"
        f"The current date and time is {now.isoformat(timespec='seconds')} "
        f"({now.strftime('%A')}). Resolve any relative dates or times the user gives "
        "(e.g. 'tomorrow', 'next Monday at 2pm') against this, and pass fully-qualified "
        "ISO 8601 datetimes to tools."
    )


class Assistant:
    """Stores conversation history and runs the OpenAI + tool execution loop"""

    def __init__(self):
        # Start the conversation with just the system prompt -- this list is the assistant's whole memory.
        self.messages = [{"role": "system", "content": _system_prompt()}]

    def send(self, user_message: str, on_tool_call=None) -> str:
        """Sends a user message, runs any tool calls, and returns the assistant's reply.

        on_tool_call(name: str), if given, is invoked right before each tool executes.
        """
        self.messages.append({"role": "user", "content": user_message})

        for _ in range(MAX_TOOL_ITERATIONS):  # allow a few rounds of tool calls, but not forever
            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,  # resend the whole conversation every time -- the API has no memory of its own
                tools=TOOLS,
            )
            message = response.choices[0].message

            if not message.tool_calls:
                # Model gave a plain text answer -- save it and we're done for this turn.
                self.messages.append({"role": "assistant", "content": message.content})
                return message.content

            # Model asked to run one or more tools -- record that request before recording its results,
            # since the API expects to see "I asked for X" before "here's the result of X".
            self.messages.append(message.model_dump(exclude_unset=True))

            for tool_call in message.tool_calls:  # a single turn can request more than one tool call
                name = tool_call.function.name
                if on_tool_call:
                    on_tool_call(name)  # lets main.py print "[calling get_info...]"
                try:
                    args = json.loads(tool_call.function.arguments)  # arguments arrive as a JSON string; parse to a dict
                    func = TOOL_IMPLEMENTATIONS[name]  # look up the real function by its name
                    result = func(**args)  # call it, unpacking the dict as keyword arguments
                except Exception as exc:
                    # Any failure here (bad JSON, bad arguments, a bug inside the tool) becomes an
                    # error message instead of crashing the whole assistant.
                    result = {"error": f"tool '{name}' failed: {exc}"}

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,  # ties this result back to the specific call that asked for it
                        "content": json.dumps(result, default=str),  # tool content must be a string, so serialize it
                    }
                )
            # Loop repeats: next call resends this tool result so the model can react to it.

        # Ran out of allowed rounds without a plain answer -- give up gracefully instead of looping forever.
        fallback = (
            "I wasn't able to finish that after several tool calls — "
            "could you clarify what you'd like me to do?"
        )
        self.messages.append({"role": "assistant", "content": fallback})
        return fallback
