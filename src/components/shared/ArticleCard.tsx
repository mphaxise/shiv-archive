"use client";

import { motion } from "framer-motion";

import { toneColor } from "@/lib/tone-style";
import { ShiftProjectionRecord } from "@/lib/types";

function formatDate(dateIso: string): string {
  const date = new Date(`${dateIso}T00:00:00Z`);
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function truncateSummary(text: string, maxChars: number): string {
  if (text.length <= maxChars) {
    return text;
  }
  const slice = text.slice(0, maxChars);
  const lastSpace = slice.lastIndexOf(" ");
  const cutoff = lastSpace > maxChars * 0.6 ? lastSpace : maxChars;
  return `${slice.slice(0, cutoff).trimEnd()}...`;
}

export function ArticleCard({
  record,
  variant = "shift",
}: {
  record: ShiftProjectionRecord;
  variant?: "shift" | "archive";
}) {
  const color = toneColor(record.analysis.tone);
  const tags = record.analysis.tags.slice(0, 3);
  const fullSummary = record.analysis.summary ?? "Summary pending.";
  const isEPW = record.meta.publication === "Economic and Political Weekly";
  const maxSummaryChars =
    variant === "archive"
      ? isEPW
        ? 180
        : 250
      : isEPW
        ? 220
        : 300;
  const cardSummary = truncateSummary(fullSummary, maxSummaryChars);

  return (
    <motion.article
      layout
      layoutId={`article-${record.article_id}`}
      className="articleCard"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ type: "spring", stiffness: 250, damping: 28 }}
    >
      <header className="articleCardTop">
        <span className="toneChip" style={{ borderColor: color, color }}>
          {(record.analysis.tone ?? "Perspective").toUpperCase()}
        </span>
        <p className="cardDate">{formatDate(record.meta.date_iso)}</p>
      </header>

      <div className="metaRow">
        <div className="metaChips">
          <span className="publicationChip">{record.meta.publication || "Publication"}</span>
          <span className="sectionChip">{record.meta.section || "Opinion"}</span>
        </div>
        {record.meta.reading_minutes ? <span className="readMeta">{record.meta.reading_minutes} min read</span> : null}
      </div>

      <h3 className="cardTitle">
        {record.meta.url ? (
          <a href={record.meta.url} target="_blank" rel="noreferrer">
            {record.meta.title}
          </a>
        ) : (
          record.meta.title
        )}
      </h3>

      <p className="cardSummary" title={fullSummary}>
        {cardSummary}
      </p>

      <footer className="cardFoot">
        <div className="tagRow">
          {tags.map((tag) => (
            <span className="tagPill" key={`${record.article_id}-${tag.slug}`}>
              {tag.label}
            </span>
          ))}
        </div>
        {variant === "shift" ? (
          <div className="phaseContext">
            <p className="phaseNote">
              <strong>
                {record.shift_context.phase === "before" ? "Phase 1 connection:" : "Phase 2 connection:"}
              </strong>{" "}
              {record.shift_context.narrative_note}
            </p>
            <p className="phaseKey">
              <strong>Key message:</strong> {record.shift_context.key_message}
            </p>
          </div>
        ) : null}
      </footer>
    </motion.article>
  );
}
