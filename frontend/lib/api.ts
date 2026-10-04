// The only place that talks to the Python backend. Everything else in the
// app calls sendMessage() instead of using fetch() directly, so if the
// backend's address or shape ever changes, this is the one file to update.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ChatResponse = {
  reply: string;
  tool_calls: string[];
};

export async function sendMessage(message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }

  return res.json();
}

export type UploadResponse = {
  file_name: string;
  chunks_stored: number;
};

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/upload`, {
    method: "POST",
    body: formData, // no Content-Type header -- the browser sets the multipart boundary itself
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Upload failed: ${res.status}`);
  }

  return res.json();
}
