"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";

import { OpinionEvidenceCard, OpinionEvidenceCardData } from "@/components/shared/OpinionEvidenceCard";
import { buildShiftSplit } from "@/lib/shift-engine";
import { SHIFT_DEFINITIONS } from "@/lib/shift-definitions";
import { RawArticleRecord, ShiftProjectionRecord } from "@/lib/types";
import { useResearchState } from "@/state/research-state";

function firstSentence(text: string | null): string {
  const normalized = (text ?? "").replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "Summary pending.";
  }
  const match = normalized.match(/^(.+?[.!?])(\s|$)/);
  return (match?.[1] ?? normalized).trim();
}

function shrink(text: string, maxChars: number): string {
  const clean = text.trim();
  if (clean.length <= maxChars) {
    return clean;
  }
  const chunk = clean.slice(0, maxChars);
  const cut = chunk.lastIndexOf(" ");
  if (cut > maxChars * 0.62) {
    return `${chunk.slice(0, cut)}...`;
  }
  return `${chunk.trimEnd()}...`;
}

function scoreToStrength(score: number): "strong" | "moderate" | "weak" {
  if (score >= 7) {
    return "strong";
  }
  if (score >= 4) {
    return "moderate";
  }
  return "weak";
}

function toOpinionEvidenceCard(record: ShiftProjectionRecord): OpinionEvidenceCardData {
  const summarySentence = firstSentence(record.analysis.summary);
  const takeawaySentence = firstSentence(record.shift_context.key_message);

  return {
    id: record.article_id,
    title: record.meta.title,
    dateIso: record.meta.date_iso,
    url: record.meta.url,
    publication: record.meta.publication,
    section: record.meta.section,
    readingMinutes: record.meta.reading_minutes,
    tone: record.analysis.tone,
    tags: record.analysis.tags.slice(0, 3).map((tag) => tag.label),
    summary: shrink(summarySentence, 220),
    takeaway: shrink(takeawaySentence, 210),
    quoteText: summarySentence === "Summary pending." ? record.meta.title : summarySentence,
    phase: record.shift_context.phase,
    connection: record.shift_context.narrative_note,
    rationale: record.shift_context.key_message,
    strengthLabel: scoreToStrength(record.score),
    relevanceScore: Number(record.score.toFixed(1)),
    quoteSource: "summary_sentence",
  };
}

export function OpinionShiftView({ articles }: { articles: RawArticleRecord[] }) {
  const { state } = useResearchState();
  const shift = SHIFT_DEFINITIONS[state.activeShift];

  if (shift.id !== "republic_shift") {
    return (
      <motion.section
        layout
        layoutId="layer-opinion-shift"
        className="layerPanel"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 12 }}
        transition={{ duration: 0.28, ease: "easeOut" }}
      >
        <header className="layerHeader">
          <p className="layerKicker">Opinion Shift</p>
          <h2>{shift.label} is queued for a future release.</h2>
          <p className="layerMeta">
            Version 1 is focused on a deeper Republic Shift reading. Ecological, Science, and
            Political shifts are parked for the next iteration.
          </p>
        </header>
      </motion.section>
    );
  }

  const split = buildShiftSplit(
    articles,
    shift,
    state.activeFilter.searchTerm,
    state.activeFilter.year
  );

  return (
    <motion.section
      layout
      layoutId="layer-opinion-shift"
      className="layerPanel"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
    >
      <header className="layerHeader">
        <p className="layerKicker">Deep Analysis</p>
        <h2>{shift.label}</h2>
        <p className="layerMeta">
          {shift.changeSummary}
          <br />
          <strong>From:</strong> {shift.fromStatement}
          <br />
          <strong>To:</strong> {shift.toStatement}
        </p>
        <Link href="/deep-analysis/republic-shift" className="analysisNarrativeLink">
          Open interactive narrative article
        </Link>
      </header>

      <div className="dialecticGrid">
        <motion.section layout className="phaseColumn">
          <h3>Phase 1: The Departure</h3>
          <p className="phaseSubtitle">{shift.beforeNarrative}</p>
          <AnimatePresence mode="popLayout">
            {split.before.map((record) => (
              <OpinionEvidenceCard
                key={record.article_id}
                layoutId={`shift-${record.article_id}`}
                data={toOpinionEvidenceCard(record)}
              />
            ))}
          </AnimatePresence>
        </motion.section>

        <motion.div layout className="pivotColumn" layoutId={`pivot-${shift.id}`}>
          <div className="pivotLine" />
          <div className="pivotBadge">
            <span>Milestone</span>
            <strong>{shift.milestoneYear}</strong>
          </div>
          <p className="pivotSummary">{shift.changeSummary}</p>
          <p className="pivotCount">{split.total} records in active lens</p>
        </motion.div>

        <motion.section layout className="phaseColumn">
          <h3>Phase 2: The Arrival</h3>
          <p className="phaseSubtitle">{shift.afterNarrative}</p>
          <AnimatePresence mode="popLayout">
            {split.after.map((record) => (
              <OpinionEvidenceCard
                key={record.article_id}
                layoutId={`shift-${record.article_id}`}
                data={toOpinionEvidenceCard(record)}
              />
            ))}
          </AnimatePresence>
        </motion.section>
      </div>
    </motion.section>
  );
}
