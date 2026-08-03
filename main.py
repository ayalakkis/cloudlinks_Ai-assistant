"""CLI entry point: REPL loop over the Assistant."""

from assistant import Assistant
from db import init_db


def main():
    """Runs the command-line chat loop: set up the database, then read/respond forever."""
    init_db()  # make sure the tables exist before we start
    assistant = Assistant()  # one Assistant for the whole session, so it remembers earlier turns

    print("Assistant ready. Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input("You: ").strip()  # wait for you to type something, trim extra whitespace
        if not user_input:
            continue  # ignore blank input, don't waste an API call on it
        if user_input.lower() in ("exit", "quit"):
            break  # end the program

        def on_tool_call(name):
            print(f"[calling {name}...]")  # shows you live when a tool is being used

        reply = assistant.send(user_input, on_tool_call=on_tool_call)
        print(f"Bot: {reply}\n")


if __name__ == "__main__":
    main()  # only run the loop if this file was started directly, not if it's imported elsewhere
