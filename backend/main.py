from assistant import Assistant
from db import init_db


def main():
    init_db()
    assistant = Assistant()

    print("Assistant ready. Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break

        def on_tool_call(name):
            print(f"[calling {name}...]")

        reply = assistant.send(user_input, on_tool_call=on_tool_call)
        print(f"Bot: {reply}\n")


if __name__ == "__main__":
    main()
