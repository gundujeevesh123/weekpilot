// Tiny, dependency-free, XSS-safe Markdown renderer for assistant replies.
// It deliberately supports only what WeekPilot's agent emits — headings, bold,
// inline `code`, bullet/numbered lists, tables, and paragraphs — and NEVER uses
// dangerouslySetInnerHTML, so model output can't inject markup.

import { type ReactNode } from "react";

// ---------- Inline (bold + code) ----------
function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  // Split on **bold** and `code`, keeping delimiters via capture groups.
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  parts.forEach((part, i) => {
    if (!part) return;
    const key = `${keyPrefix}-${i}`;
    if (part.startsWith("**") && part.endsWith("**")) {
      nodes.push(<strong key={key}>{part.slice(2, -2)}</strong>);
    } else if (part.startsWith("`") && part.endsWith("`")) {
      nodes.push(<code key={key}>{part.slice(1, -1)}</code>);
    } else {
      nodes.push(<span key={key}>{part}</span>);
    }
  });
  return nodes;
}

function isTableSep(line: string): boolean {
  // |---|:--:|---| style separator row
  return /^\s*\|?[\s:|-]+\|?\s*$/.test(line) && line.includes("-");
}

function splitRow(line: string): string[] {
  let s = line.trim();
  if (s.startsWith("|")) s = s.slice(1);
  if (s.endsWith("|")) s = s.slice(0, -1);
  return s.split("|").map((c) => c.trim());
}

// ---------- Block renderer ----------
export function Markdown({ text }: { text: string }) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Blank line → skip
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Table: a header row followed by a separator row
    if (
      line.includes("|") &&
      i + 1 < lines.length &&
      isTableSep(lines[i + 1])
    ) {
      const header = splitRow(line);
      const rows: string[][] = [];
      i += 2;
      while (i < lines.length && lines[i].includes("|") && lines[i].trim() !== "") {
        rows.push(splitRow(lines[i]));
        i++;
      }
      blocks.push(
        <div className="md-table-wrap" key={`tbl-${key++}`}>
          <table className="md-table">
            <thead>
              <tr>
                {header.map((h, hi) => (
                  <th key={hi}>{renderInline(h, `th-${hi}`)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, ri) => (
                <tr key={ri}>
                  {header.map((_, ci) => (
                    <td key={ci}>{renderInline(r[ci] ?? "", `td-${ri}-${ci}`)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    // Heading
    const h = /^(#{1,4})\s+(.*)$/.exec(line);
    if (h) {
      const level = h[1].length;
      const content = renderInline(h[2], `h-${key}`);
      const Tag = (`h${Math.min(level + 2, 6)}`) as keyof JSX.IntrinsicElements;
      blocks.push(
        <Tag className="md-h" key={`h-${key++}`}>
          {content}
        </Tag>
      );
      i++;
      continue;
    }

    // Bullet list
    if (/^\s*[-*]\s+/.test(line)) {
      const items: ReactNode[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        const item = lines[i].replace(/^\s*[-*]\s+/, "");
        items.push(<li key={items.length}>{renderInline(item, `li-${key}-${items.length}`)}</li>);
        i++;
      }
      blocks.push(
        <ul className="md-ul" key={`ul-${key++}`}>
          {items}
        </ul>
      );
      continue;
    }

    // Numbered list
    if (/^\s*\d+\.\s+/.test(line)) {
      const items: ReactNode[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        const item = lines[i].replace(/^\s*\d+\.\s+/, "");
        items.push(<li key={items.length}>{renderInline(item, `ol-${key}-${items.length}`)}</li>);
        i++;
      }
      blocks.push(
        <ol className="md-ol" key={`ol-${key++}`}>
          {items}
        </ol>
      );
      continue;
    }

    // Paragraph (gather consecutive non-block lines)
    const para: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i]) &&
      !/^(#{1,4})\s+/.test(lines[i]) &&
      !(lines[i].includes("|") && i + 1 < lines.length && isTableSep(lines[i + 1]))
    ) {
      para.push(lines[i]);
      i++;
    }
    blocks.push(
      <p className="md-p" key={`p-${key++}`}>
        {para.map((pl, pi) => (
          <span key={pi}>
            {renderInline(pl, `p-${key}-${pi}`)}
            {pi < para.length - 1 ? <br /> : null}
          </span>
        ))}
      </p>
    );
  }

  return <>{blocks}</>;
}

// ---------- Schedule-table extraction (powers the dashboard) ----------

export interface Block {
  day: string;
  time: string;
  work: string;
  notes: string;
}

export interface DayPlan {
  day: string;
  blocks: Block[];
  hours: number; // total scheduled hours that day
  weather: string; // a short weather chip (emoji/temp) if detected
}

const WEATHER_RE =
  /(☀️|🌤️|⛅|🌥️|☁️|🌦️|🌧️|⛈️|🌩️|❄️|🌨️|🌫️|💨|-?\d{1,2}\s?°\s?[CF])/u;

function parseHours(time: string): number {
  // Match "07:00–08:30", "7:00-8:30", "09:00 to 10:00"
  const m = time.match(
    /(\d{1,2}):(\d{2})\s*(?:–|-|—|to)\s*(\d{1,2}):(\d{2})/
  );
  if (!m) return 0;
  const start = parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
  let end = parseInt(m[3], 10) * 60 + parseInt(m[4], 10);
  if (end < start) end += 24 * 60; // crosses midnight
  return Math.max(0, (end - start) / 60);
}

// Find the FIRST markdown table whose header looks like Day/Time/Work/Notes and
// return it grouped by day. Returns null if the text has no such table.
export function parseScheduleTable(text: string): DayPlan[] | null {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  for (let i = 0; i < lines.length - 1; i++) {
    if (!lines[i].includes("|") || !isTableSep(lines[i + 1])) continue;
    const header = splitRow(lines[i]).map((h) => h.toLowerCase());
    const dayIdx = header.findIndex((h) => h.includes("day"));
    const timeIdx = header.findIndex((h) => h.includes("time"));
    const workIdx = header.findIndex(
      (h) => h.includes("work") || h.includes("activity") || h.includes("task")
    );
    if (dayIdx === -1 || timeIdx === -1 || workIdx === -1) continue;
    const notesIdx = header.findIndex(
      (h) => h.includes("note") || h.includes("weather") || h.includes("detail")
    );

    const rows: Block[] = [];
    let j = i + 2;
    while (j < lines.length && lines[j].includes("|") && lines[j].trim() !== "") {
      const cells = splitRow(lines[j]);
      const day = (cells[dayIdx] ?? "").trim();
      const time = (cells[timeIdx] ?? "").trim();
      const work = (cells[workIdx] ?? "").trim();
      const notes = notesIdx >= 0 ? (cells[notesIdx] ?? "").trim() : "";
      if (day || time || work) rows.push({ day, time, work, notes });
      j++;
    }
    if (rows.length === 0) return null;

    // Group consecutive rows by day, preserving order.
    const byDay = new Map<string, DayPlan>();
    const order: string[] = [];
    for (const r of rows) {
      const key = r.day || "—";
      if (!byDay.has(key)) {
        byDay.set(key, { day: key, blocks: [], hours: 0, weather: "" });
        order.push(key);
      }
      const dp = byDay.get(key)!;
      dp.blocks.push(r);
      dp.hours += parseHours(r.time);
      if (!dp.weather) {
        const w = (r.notes.match(WEATHER_RE) || [])[0];
        if (w) dp.weather = w.trim();
      }
    }
    return order.map((k) => byDay.get(k)!);
  }
  return null;
}
