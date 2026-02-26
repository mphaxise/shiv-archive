"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";

import { OpinionEvidenceCard, OpinionEvidenceCardData } from "@/components/shared/OpinionEvidenceCard";
import scienceShiftStory from "@/data/science_shift_story_2026-02-26.json";
import { buildShiftSplit } from "@/lib/shift-engine";
import { SHIFT_DEFINITIONS } from "@/lib/shift-definitions";
import { RawArticleRecord, ShiftProjectionRecord } from "@/lib/types";
import { useResearchState } from "@/state/research-state";

interface ScienceStoryRecord {
  article_uid: string;
  phase: "before" | "after";
  published_date: string;
  url: string | null;
  publication: string;
  title: string;
  summary_snippet: string;
  signal_tags: string[];
  group_hits?: Record<string, number | undefined>;
  connection_text: string;
  rationale: string;
  quote_text: string;
  quote_source: "body_paragraph" | "summary_sentence" | "title";
  include_in_story: boolean;
  relevance_score: number;
  strength_label: "strong" | "moderate" | "weak";
}

interface ScienceShiftStoryPayload {
  selected_records: ScienceStoryRecord[];
}

function normalizeText(text: string | null | undefined): string {
  return (text ?? "").replace(/\s+/g, " ").trim();
}

function leadingSentence(text: string | null | undefined): string {
  const normalized = normalizeText(text);
  if (!normalized) {
    return "";
  }
  const match = normalized.match(/^(.+?[.!?])(\s|$)/);
  return (match?.[1] ?? normalized).trim();
}

function stripRepeatedLead(text: string, lead: string): string {
  if (!text || !lead) {
    return text;
  }
  const textLower = text.toLowerCase();
  const leadLower = lead.toLowerCase();
  if (!textLower.startsWith(leadLower)) {
    return text;
  }
  return text.slice(lead.length).replace(/^[\s,.:;/-]+/, "").trim();
}

function splitSentences(text: string): string[] {
  return text
    .match(/[^.!?]+(?:[.!?]+|$)/g)
    ?.map((sentence) => sentence.trim())
    .filter(Boolean) ?? [];
}

function punctuate(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) {
    return "";
  }
  return /[.!?]$/.test(trimmed) ? trimmed : `${trimmed}.`;
}

function buildCardSummary(summary: string | null | undefined, contextFallback: string): string {
  const normalizedSummary = normalizeText(summary);
  if (!normalizedSummary) {
    const fallbackLead = leadingSentence(contextFallback);
    return fallbackLead ? punctuate(fallbackLead) : "Summary pending.";
  }

  const summarySentences = splitSentences(normalizedSummary);
  if (summarySentences.length >= 2) {
    return `${summarySentences[0]} ${summarySentences[1]}`.trim();
  }

  const first = summarySentences[0] ?? punctuate(normalizedSummary);
  const fallbackLead = leadingSentence(contextFallback);
  if (fallbackLead && fallbackLead.toLowerCase() !== first.toLowerCase()) {
    return `${punctuate(first)} ${punctuate(fallbackLead)}`.trim();
  }

  return punctuate(first);
}

function deriveTakeaway(summaryText: string, keyMessage: string, connection: string): string {
  const summaryLead = leadingSentence(summaryText === "Summary pending." ? "" : summaryText);
  const cleanedKeyMessage = normalizeText(keyMessage);
  const dedupedKeyMessage = stripRepeatedLead(cleanedKeyMessage, summaryLead);
  const keyMessageLead = leadingSentence(dedupedKeyMessage);
  if (keyMessageLead) {
    return keyMessageLead;
  }

  const connectionLead = leadingSentence(connection);
  if (connectionLead) {
    return connectionLead;
  }

  return "Takeaway pending.";
}

const SCIENCE_ARGUMENT_BY_GROUP: Record<"before" | "after", Record<string, string>> = {
  before: {
    institutional_knowledge:
      "The article argues that institutional expertise has become gatekeeping, narrowing science's democratic dialogue.",
    diagnosing_closure:
      "The article argues that bureaucratic science has become conceptually exhausted and cannot handle public complexity.",
    democratic_learning:
      "The article argues for science as a democratic commons sustained by dissent and public reasoning.",
  },
  after: {
    distributed_publics:
      "The article argues for redistributing scientific authority through knowledge panchayats and plural publics.",
    playful_science:
      "The article argues that playful experimentation, not managerial Big Science, drives living scientific imagination.",
    ethics_of_knowledge:
      "The article argues that science must answer to conscience, care, and social repair, not efficiency alone.",
  },
};

function strongestScienceGroup(record: ScienceStoryRecord): string | null {
  const entries = Object.entries(record.group_hits ?? {});
  if (entries.length === 0) {
    return null;
  }
  let bestGroup = "";
  let bestScore = 0;
  for (const [group, rawScore] of entries) {
    const score = Number(rawScore ?? 0);
    if (score > bestScore) {
      bestGroup = group;
      bestScore = score;
    }
  }
  return bestGroup || null;
}

function buildScienceTakeaway(record: ScienceStoryRecord, summaryText: string): string {
  const strongestGroup = strongestScienceGroup(record);
  const groupArgument = strongestGroup
    ? SCIENCE_ARGUMENT_BY_GROUP[record.phase][strongestGroup]
    : undefined;

  if (groupArgument) {
    return groupArgument;
  }

  return deriveTakeaway(summaryText, record.rationale, record.connection_text);
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

function slugToLabel(slug: string): string {
  return slug
    .split("-")
    .filter(Boolean)
    .map((word) => {
      if (word.length <= 3) {
        return word.toUpperCase();
      }
      return `${word[0].toUpperCase()}${word.slice(1)}`;
    })
    .join(" ");
}

function compareCardChronological(a: OpinionEvidenceCardData, b: OpinionEvidenceCardData): number {
  const byDate = a.dateIso.localeCompare(b.dateIso);
  if (byDate !== 0) {
    return byDate;
  }
  return a.title.localeCompare(b.title);
}

function buildScienceShiftCards(
  articles: RawArticleRecord[],
  searchTerm: string,
  yearFilter: "all" | number
): { before: OpinionEvidenceCardData[]; after: OpinionEvidenceCardData[]; total: number } {
  const packet = scienceShiftStory as unknown as ScienceShiftStoryPayload;
  const selected = packet.selected_records.filter((record) => record.include_in_story);

  const articleByUid = new Map<string, RawArticleRecord>();
  for (const article of articles) {
    if (article.article_uid) {
      articleByUid.set(article.article_uid, article);
    }
  }

  const cards = selected.map((record) => {
    const matched = articleByUid.get(record.article_uid);
    const labelBySlug = new Map((matched?.tags ?? []).map((tag) => [tag.slug, tag.label]));
    const curatedTags =
      record.signal_tags.length > 0
        ? record.signal_tags.map((slug) => labelBySlug.get(slug) ?? slugToLabel(slug))
        : (matched?.tags ?? []).slice(0, 3).map((tag) => tag.label);
    const summaryText = buildCardSummary(matched?.summary ?? record.summary_snippet, record.connection_text);
    const scienceTakeaway = buildScienceTakeaway(record, summaryText);

    return {
      id: record.article_uid,
      title: record.title,
      dateIso: record.published_date,
      url: record.url ?? matched?.url ?? null,
      publication: record.publication || matched?.publication || "Unknown publication",
      section: matched?.section ?? "Opinion",
      readingMinutes: matched?.reading_minutes ?? null,
      tone: matched?.tone ?? "Perspective",
      tags: curatedTags,
      summary: shrink(summaryText, 320),
      takeaway: shrink(scienceTakeaway, 210),
      quoteText: record.quote_text?.trim() || record.title,
      phase: record.phase,
      connection: record.connection_text,
      rationale: record.rationale,
      strengthLabel: record.strength_label,
      relevanceScore: record.relevance_score,
      quoteSource: record.quote_source,
    } satisfies OpinionEvidenceCardData;
  });

  const searchProbe = searchTerm.trim().toLowerCase();
  const searched =
    searchProbe.length === 0
      ? cards
      : cards.filter((card) =>
          [
            card.title,
            card.summary,
            card.takeaway,
            card.quoteText,
            card.publication,
            card.connection,
            card.rationale,
            card.tags.join(" "),
          ]
            .join(" ")
            .toLowerCase()
            .includes(searchProbe)
        );

  const yearFiltered =
    yearFilter === "all"
      ? searched
      : searched.filter((card) => Number(card.dateIso.slice(0, 4)) === yearFilter);

  const before = yearFiltered
    .filter((card) => card.phase === "before")
    .sort(compareCardChronological);
  const after = yearFiltered
    .filter((card) => card.phase === "after")
    .sort(compareCardChronological);

  return {
    before,
    after,
    total: yearFiltered.length,
  };
}

function toOpinionEvidenceCard(record: ShiftProjectionRecord): OpinionEvidenceCardData {
  const summaryText = buildCardSummary(record.analysis.summary, record.shift_context.narrative_note);
  const takeawaySentence = deriveTakeaway(
    summaryText,
    record.shift_context.key_message,
    record.shift_context.narrative_note
  );
  const summaryLead = leadingSentence(summaryText);

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
    summary: shrink(summaryText, 320),
    takeaway: shrink(takeawaySentence, 210),
    quoteText: summaryLead || record.meta.title,
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
  const activeLongformShift = shift.id === "republic_shift" || shift.id === "science_shift";
  const narrativeHref =
    shift.id === "science_shift" ? "/deep-analysis/science-shift" : "/deep-analysis/republic-shift";

  if (!activeLongformShift) {
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
            Deep narrative reads are currently active for the Republic and Science shifts.
            Ecological and Political long-form tracks are queued for the next iteration.
          </p>
        </header>
      </motion.section>
    );
  }

  let beforeCards: OpinionEvidenceCardData[];
  let afterCards: OpinionEvidenceCardData[];
  let totalRecords: number;

  if (shift.id === "science_shift") {
    const scienceCards = buildScienceShiftCards(
      articles,
      state.activeFilter.searchTerm,
      state.activeFilter.year
    );
    beforeCards = scienceCards.before;
    afterCards = scienceCards.after;
    totalRecords = scienceCards.total;
  } else {
    const split = buildShiftSplit(articles, shift, state.activeFilter.searchTerm, state.activeFilter.year);
    beforeCards = split.before.map((record) => toOpinionEvidenceCard(record));
    afterCards = split.after.map((record) => toOpinionEvidenceCard(record));
    totalRecords = split.total;
  }

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
        <Link href={narrativeHref} className="analysisNarrativeLink">
          Open long-form narrative article
        </Link>
      </header>

      <div className="dialecticGrid">
        <motion.section layout className="phaseColumn">
          <h3>Phase 1: The Departure</h3>
          <p className="phaseSubtitle">{shift.beforeNarrative}</p>
          <AnimatePresence mode="popLayout">
            {beforeCards.map((card) => (
              <OpinionEvidenceCard
                key={card.id}
                layoutId={`shift-${card.id}`}
                data={card}
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
          <p className="pivotCount">{totalRecords} records in active lens</p>
        </motion.div>

        <motion.section layout className="phaseColumn">
          <h3>Phase 2: The Arrival</h3>
          <p className="phaseSubtitle">{shift.afterNarrative}</p>
          <AnimatePresence mode="popLayout">
            {afterCards.map((card) => (
              <OpinionEvidenceCard
                key={card.id}
                layoutId={`shift-${card.id}`}
                data={card}
              />
            ))}
          </AnimatePresence>
        </motion.section>
      </div>
    </motion.section>
  );
}
