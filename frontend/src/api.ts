// Tiny typed client for the WeekPilot backend. Only the user's message text is
// ever sent — no keys or personal config live in the browser.

export interface ChatResponse {
  session_id: string;
  reply: string;
}

export async function sendChat(
  message: string,
  sessionId: string | null
): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!res.ok) {
    let detail = "Something went wrong. Please try again.";
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") detail = body.detail;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }

  return res.json() as Promise<ChatResponse>;
}
