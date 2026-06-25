import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEvent,
} from "react";
import { sendChat } from "./api";
import { Markdown, parseScheduleTable, type DayPlan } from "./markdown";

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

// A pre-filled sample so the dashboard is never a blank page (2026 UX best practice).
const SAMPLE_WEEK: DayPlan[] = [
  {
    day: "Monday",
    weather: "☀️ 19°C",
    hours: 6,
    blocks: [
      { day: "Monday", time: "07:00–08:00", work: "🏋️ Gym", notes: "☀️ Clear — great to train" },
      { day: "Monday", time: "09:00–12:00", work: "💻 Deep work: Q3 proposal", notes: "High priority" },
      { day: "Monday", time: "14:00–16:00", work: "📞 Client calls", notes: "" },
    ],
  },
  {
    day: "Wednesday",
    weather: "🌦️ 15°C",
    hours: 4.5,
    blocks: [
      { day: "Wednesday", time: "07:00–08:00", work: "🏋️ Gym", notes: "🌦️ Showers — indoor day" },
      { day: "Wednesday", time: "10:00–12:30", work: "💻 Deep work", notes: "Focus block" },
      { day: "Wednesday", time: "13:00–14:00", work: "🍽️ Lunch with team", notes: "" },
    ],
  },
  {
    day: "Friday",
    weather: "⛅ 17°C",
    hours: 5,
    blocks: [
      { day: "Friday", time: "09:00–12:00", work: "💻 Wrap-up & review", notes: "" },
      { day: "Friday", time: "13:00–14:00", work: "✅ Weekly shutdown", notes: "Plan next week" },
      { day: "Friday", time: "19:00–20:00", work: "🍽️ Dinner with Sam", notes: "⛅ Mild evening" },
    ],
  },
];

function uid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
}

function fmtHours(h: number): string {
  if (h <= 0) return "—";
  return Number.isInteger(h) ? `${h}h` : `${h.toFixed(1)}h`;
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [week, setWeek] = useState<DayPlan[]>(SAMPLE_WEEK);
  const [isSample, setIsSample] = useState(true);
  const [mobileView, setMobileView] = useState<"dashboard" | "chat">("chat");
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

  // Dashboard summary stats.
  const stats = useMemo(() => {
    const totalHours = week.reduce((s, d) => s + d.hours, 0);
    const totalBlocks = week.reduce((s, d) => s + d.blocks.length, 0);
    const busiest = week.reduce<DayPlan | null>(
      (b, d) => (b === null || d.hours > b.hours ? d : b),
      null
    );
    return {
      days: week.length,
      totalBlocks,
      totalHours,
      busiest: busiest?.day ?? "—",
      overloaded: week.filter((d) => d.hours > 8).map((d) => d.day),
    };
  }, [week]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setMessages((m) => [...m, { id: uid(), role: "user", text: trimmed }]);
    setInput("");
    if (taRef.current) taRef.current.style.height = "auto";
    setLoading(true);
    setMobileView("chat");

    try {
      const res = await sendChat(trimmed, sessionId);
      setSessionId(res.session_id);
      setMessages((m) => [...m, { id: uid(), role: "assistant", text: res.reply }]);

      // Lift any schedule table in the reply into the live dashboard.
      const parsed = parseScheduleTable(res.reply);
      if (parsed && parsed.length) {
        setWeek(parsed);
        setIsSample(false);
        setMobileView("dashboard");
      }
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
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }

  function newChat() {
    setMessages([]);
    setSessionId(null);
    setInput("");
    setLoading(false);
    setWeek(SAMPLE_WEEK);
    setIsSample(true);
  }

  const emptyChat = messages.length === 0;

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
          <span className="privacy-badge" title="Your data stays in your session — nothing is sold or stored to disk">
            <span aria-hidden>🔒</span> Privacy-first
          </span>
          <button className="ghost-btn" onClick={newChat} title="Start a new conversation">
            <span aria-hidden>✨</span> <span className="lbl">New chat</span>
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

      {/* Mobile tab switch */}
      <div className="mobile-tabs">
        <button
          className={mobileView === "dashboard" ? "active" : ""}
          onClick={() => setMobileView("dashboard")}
        >
          📅 My Week
        </button>
        <button
          className={mobileView === "chat" ? "active" : ""}
          onClick={() => setMobileView("chat")}
        >
          💬 Chat
        </button>
      </div>

      <div className="layout">
        {/* ---------------- Dashboard ---------------- */}
        <section className={`dashboard ${mobileView === "dashboard" ? "show" : ""}`}>
          <div className="dash-head">
            <h2>📅 My Week</h2>
            {isSample && <span className="sample-tag">Sample · ask me to plan your week</span>}
          </div>

          <div className="stat-grid">
            <div className="stat">
              <span className="stat-num">{stats.days}</span>
              <span className="stat-lbl">days planned</span>
            </div>
            <div className="stat">
              <span className="stat-num">{stats.totalBlocks}</span>
              <span className="stat-lbl">blocks</span>
            </div>
            <div className="stat">
              <span className="stat-num">{fmtHours(stats.totalHours)}</span>
              <span className="stat-lbl">scheduled</span>
            </div>
            <div className="stat">
              <span className="stat-num">{stats.busiest}</span>
              <span className="stat-lbl">busiest day</span>
            </div>
          </div>

          {stats.overloaded.length > 0 && (
            <div className="overload-warn">
              ⚠️ Heavy load on <strong>{stats.overloaded.join(", ")}</strong> (8h+). Consider moving a block.
            </div>
          )}

          <div className="week-card">
            <table className="week-table">
              <thead>
                <tr>
                  <th>Day</th>
                  <th>Time</th>
                  <th>Work</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {week.map((d) =>
                  d.blocks.map((b, bi) => (
                    <tr key={`${d.day}-${bi}`} className={bi === 0 ? "day-start" : ""}>
                      {bi === 0 && (
                        <td className="day-cell" rowSpan={d.blocks.length}>
                          <div className="day-name">{d.day}</div>
                          {d.weather && <div className="day-weather">{d.weather}</div>}
                          <div className={`day-load ${d.hours > 8 ? "hot" : ""}`}>
                            <span
                              className="day-load-bar"
                              style={{ width: `${Math.min(100, (d.hours / 10) * 100)}%` }}
                            />
                            <span className="day-load-txt">{fmtHours(d.hours)}</span>
                          </div>
                        </td>
                      )}
                      <td className="time-cell">{b.time}</td>
                      <td className="work-cell">{b.work}</td>
                      <td className="notes-cell">{b.notes || <span className="dim">—</span>}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <p className="dash-hint">
            💡 Tell the chat “plan my week…” and this table updates automatically.
          </p>
        </section>

        {/* ---------------- Chat ---------------- */}
        <section className={`chat-panel ${mobileView === "chat" ? "show" : ""}`}>
          <div className="chat">
            {emptyChat ? (
              <div className="hero">
                <div className="hero-badge" aria-hidden>🚀</div>
                <h2>Plan your week in plain words</h2>
                <p>
                  Tell me your tasks, meetings, and ideas — I'll triage, schedule,
                  draft messages, and check the weather. Watch <strong>My Week</strong> fill in live.
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
                      {m.role === "assistant" && !m.error ? (
                        <div className="bubble-text">
                          <Markdown text={m.text} />
                        </div>
                      ) : (
                        <div className="bubble-text plain">{m.text}</div>
                      )}
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
          </div>

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
        </section>
      </div>
    </div>
  );
}
