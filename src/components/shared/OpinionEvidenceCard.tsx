"use client";

import { motion } from "framer-motion";
import { useMemo, useState } from "react";

import { toneColor } from "@/lib/tone-style";

export interface OpinionEvidenceCardData {
  id: string;
  title: string;
  dateIso: string;
  url: string | null;
  publication: string;
  section?: string | null;
  readingMinutes?: number | null;
  tone?: string | null;
  tags: string[];
  summary: string;
  takeaway: string;
  quoteText: string;
  phase: "before" | "after";
  connection: string;
  rationale: string;
  strengthLabel: "strong" | "moderate" | "weak";
  relevanceScore: number;
  quoteSource: "body_paragraph" | "summary_sentence" | "title";
}

function formatDate(dateIso: string): string {
  const date = new Date(`${dateIso}T00:00:00Z`);
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

export function OpinionEvidenceCard({
  data,
  layoutId,
}: {
  data: OpinionEvidenceCardData;
  layoutId?: string;
}) {
  const [isFlipped, setIsFlipped] = useState(false);
  const toneBorder = useMemo(() => toneColor(data.tone), [data.tone]);
  const toneLabel = (data.tone ?? "Perspective").toUpperCase();
  const sectionLabel = data.section?.trim() ? data.section : "Opinion";

  return (
    <motion.article
      layout
      layoutId={layoutId}
      className={`narrativeEvidenceCard ${isFlipped ? "isFlipped" : ""}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ type: "spring", stiffness: 250, damping: 28 }}
    >
      <div className="narrativeFlipInner">
        <section className="narrativeFlipFace narrativeFlipFront">
          <header className="narrativeEvidenceHead">
            <span className="toneChip" style={{ borderColor: toneBorder, color: toneBorder }}>
              {toneLabel}
            </span>
            <p className="narrativeEvidenceDate">{formatDate(data.dateIso)}</p>
            <button
              type="button"
              className="narrativeFlipIconButton"
              onClick={() => setIsFlipped(true)}
              aria-label={`Show strict analysis for ${data.title}`}
              title="Show strict analysis"
            >
              <span className="narrativeFlipIcon" aria-hidden="true" />
            </button>
          </header>

          <div className="metaRow">
            <div className="metaChips">
              <span className="publicationChip">{data.publication || "Publication"}</span>
              <span className="sectionChip">{sectionLabel}</span>
            </div>
            {data.readingMinutes ? <span className="readMeta">{data.readingMinutes} min read</span> : null}
          </div>

          <h3 className="narrativeEvidenceTitle">
            {data.url ? (
              <a href={data.url} target="_blank" rel="noreferrer">
                {data.title}
              </a>
            ) : (
              data.title
            )}
          </h3>

          <p className="narrativeSummary">
            <strong>Summary:</strong> {data.summary}
          </p>
          <p className="narrativeTakeaway">
            <strong>Takeaway:</strong> {data.takeaway}
          </p>
          <blockquote className="narrativeQuote">"{data.quoteText}"</blockquote>
          <div className="narrativeThemeRow">
            {data.tags.length > 0 ? (
              data.tags.map((theme) => (
                <span key={`${data.id}-${theme}`} className="narrativeThemeChip">
                  {theme}
                </span>
              ))
            ) : (
              <span className="narrativeThemeChip">Republic Shift</span>
            )}
          </div>
        </section>

        <section className="narrativeFlipFace narrativeFlipBack">
          <header className="narrativeEvidenceHead">
            <p className="narrativeEvidenceDate">{formatDate(data.dateIso)}</p>
            <p className="narrativeEvidenceSource">
              {data.phase === "before" ? "Phase 1 evidence" : "Phase 2 evidence"}
            </p>
            <button
              type="button"
              className="narrativeFlipIconButton"
              onClick={() => setIsFlipped(false)}
              aria-label={`Return to qualitative view for ${data.title}`}
              title="Back to qualitative view"
            >
              <span className="narrativeFlipIcon" aria-hidden="true" />
            </button>
          </header>
          <p className="narrativeConnection">
            <strong>Phase connection:</strong> {data.connection}
          </p>
          <p className="narrativeKeyMessage">
            <strong>Selection rationale:</strong> {data.rationale}
          </p>
          <p className="narrativeEvidenceScore">
            Strength: <strong>{data.strengthLabel}</strong> | Relevance score:{" "}
            <strong>{data.relevanceScore.toFixed(1)}</strong> | Quote source:{" "}
            <strong>{data.quoteSource}</strong>
          </p>
        </section>
      </div>
    </motion.article>
  );
}
