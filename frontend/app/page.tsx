// The home page ("/"). It just centers the chat window on a soft background.
// All the actual chat behavior lives inside <ChatWindow />.
import { ChatWindow } from "@/components/chat-window";

export default function Home() {
  return (
    <div className="flex flex-1 items-center justify-center bg-gradient-to-br from-indigo-50 via-zinc-50 to-zinc-100 p-6 dark:from-zinc-950 dark:via-black dark:to-zinc-950">
      <ChatWindow />
    </div>
  );
}
