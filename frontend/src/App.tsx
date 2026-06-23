import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEvent,
} from "react";
import { sendChat } from "./api";

type Role = "user" | "assistant";

interface Message {
  id: string;
  role: Role;
  text: string;
  error?: boolean;
}

const SUGGESTIONS: string[] = [
  "Plan my week in London: gym Mon/Wed/Fri 7am, deep-work mornings, dinner with Sam Friday — check the weather.",
  "Add tasks: finish Q3 proposal by Thursday (high priority), book dentist, reply to Sam — then prioritize them.",
  "Draft a friendly email to my manager asking for Friday off.",
  "What's the weather in Mumbai for the next 3 days?",
];

// Render **bold** spans without using dangerouslySetInnerHTML (XSS-safe).
function renderInline(text: string) {
  return text.split("**").map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : <span key={i}>{part}</span>
  );
}

function uid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">(() =>
    window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light"
  );

  const endRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setMessages((m) => [...m, { id: uid(), role: "user", text: trimmed }]);
    setInput("");
    if (taRef.current) taRef.current.style.height = "auto";
    setLoading(true);

    try {
      const res = await sendChat(trimmed, sessionId);
      setSessionId(res.session_id);
      setMessages((m) => [...m, { id: uid(), role: "assistant", text: res.reply }]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Something went wrong. Please try again.";
      setMessages((m) => [...m, { id: uid(), role: "assistant", text: msg, error: true }]);
    } finally {
      setLoading(false);
    }
  }

  function lastUserText(): string {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "user") return messages[i].text;
    }
    return "";
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  function onInput(e: ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
  }

  function newChat() {
    setMessages([]);
    setSessionId(null);
    setInput("");
    setLoading(false);
  }

  const empty = messages.length === 0;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden>🚀</span>
          <div className="brand-text">
            <h1>WeekPilot</h1>
            <p>Your privacy-first weekly concierge</p>
          </div>
        </div>
        <div className="actions">
          <button className="ghost-btn" onClick={newChat} title="Start a new conversation">
            <span aria-hidden>✨</span> New chat
          </button>
          <button
            className="icon-btn"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            title={theme === "dark" ? "Switch to light" : "Switch to dark"}
            aria-label="Toggle theme"
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
        </div>
      </header>

      <main className="chat">
        {empty ? (
          <div className="hero">
            <div className="hero-badge" aria-hidden>🚀</div>
            <h2>Plan your week in plain words</h2>
            <p>
              Tell me your tasks, meetings, and ideas — I'll triage, schedule,
              draft messages, and check the weather. Your data stays private.
            </p>
            <div className="chips">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="chip" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages">
            {messages.map((m) => (
              <div key={m.id} className={`row ${m.role}`}>
                <div className="avatar" aria-hidden>
                  {m.role === "assistant" ? "🚀" : "🧑"}
                </div>
                <div className={`bubble ${m.role}${m.error ? " error" : ""}`}>
                  <div className="bubble-text">{renderInline(m.text)}</div>
                  {m.error && (
                    <button className="retry" onClick={() => send(lastUserText())}>
                      ↻ Try again
                    </button>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="row assistant">
                <div className="avatar" aria-hidden>🚀</div>
                <div className="bubble assistant">
                  <div className="typing" aria-label="WeekPilot is thinking">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
        )}
      </main>

      <footer className="composer">
        <div className="composer-inner">
          <textarea
            ref={taRef}
            className="composer-input"
            placeholder="Message WeekPilot…  (e.g. plan my week, add a task, draft an email)"
            value={input}
            onChange={onInput}
            onKeyDown={onKeyDown}
            rows={1}
          />
          <button
            className="send-btn"
            onClick={() => send(input)}
            disabled={loading || input.trim().length === 0}
            aria-label="Send message"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden>
              <path
                fill="currentColor"
                d="M3.4 20.4l17.45-7.48a1 1 0 000-1.84L3.4 3.6a1 1 0 00-1.39 1.2L4 11l11 1-11 1-1.98 6.2a1 1 0 001.38 1.2z"
              />
            </svg>
          </button>
        </div>
        <p className="hint">
          Press <kbd>Enter</kbd> to send · <kbd>Shift</kbd>+<kbd>Enter</kbd> for a new line
        </p>
      </footer>
    </div>
  );
}
