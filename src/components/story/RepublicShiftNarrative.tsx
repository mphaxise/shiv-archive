"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import { RawArticleRecord } from "@/lib/types";

interface NarrativeRecord {
  id: string;
  title: string;
  dateIso: string;
  year: number;
  url: string | null;
  publication: string;
  summary: string | null;
  phase: "before" | "after";
  shortSummary: string;
  themes: string[];
  takeaway: string;
  connection: string;
  rationale: string;
  quoteText: string;
  relevanceScore: number;
  strengthLabel: "strong" | "moderate" | "weak";
  quoteSource: "body_paragraph" | "summary_sentence" | "title";
  includeInStory: boolean;
}

const REPUBLIC_MILESTONE_YEAR = 2024;
const CHUNK_SIZE = 8;

function formatDate(dateIso: string): string {
  const date = new Date(`${dateIso}T00:00:00Z`);
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function firstSentence(text: string | null): string {
  const normalized = (text ?? "").replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "Summary pending.";
  }
  const match = normalized.match(/^(.+?[.!?])(\s|$)/);
  return (match?.[1] ?? normalized).trim();
}

function shrink(text: string, maxChars: number): string {
  const clean = (text ?? "").trim();
  if (clean.length <= maxChars) {
    return clean;
  }
  const slice = clean.slice(0, maxChars);
  const cut = slice.lastIndexOf(" ");
  if (cut > maxChars * 0.62) {
    return `${slice.slice(0, cut)}...`;
  }
  return `${slice.trimEnd()}...`;
}

function buildTakeaway(
  phase: "before" | "after",
  keyMessage: string | undefined,
  summary: string | null
): string {
  const keySentence = firstSentence(keyMessage ?? "");
  if (keySentence && keySentence !== "Summary pending.") {
    return shrink(keySentence, 210);
  }
  const summarySentence = firstSentence(summary);
  if (summarySentence && summarySentence !== "Summary pending.") {
    return shrink(summarySentence, 210);
  }
  return phase === "before"
    ? "Highlights pressure points in First Republic institutions and democratic grammar."
    : "Signals emerging vocabularies and tensions shaping the Second Republic.";
}

function toNarrativeRecord(article: RawArticleRecord): NarrativeRecord {
  const annotation = article.shift_annotations?.republic_shift;
  const critical = article.republic_critical;
  const fallbackPhase: "before" | "after" = article.year < REPUBLIC_MILESTONE_YEAR ? "before" : "after";
  const phase = critical?.phase ?? annotation?.phase ?? fallbackPhase;
  const themes = article.tags.slice(0, 3).map((tag) => tag.label);
  const shortSummary = shrink(firstSentence(article.summary), 230);
  const takeaway = buildTakeaway(phase, annotation?.key_message, article.summary);

  return {
    id: String(article.id),
    title: article.title,
    dateIso: article.date_iso,
    year: article.year,
    url: article.url,
    publication: article.publication,
    summary: article.summary,
    phase,
    shortSummary,
    themes,
    takeaway,
    connection:
      critical?.connection_text ??
      annotation?.connection ??
      (fallbackPhase === "before"
        ? "Reads this article against the erosion of First Republic institutions."
        : "Reads this article as evidence of emerging Second Republic vocabularies."),
    rationale:
      critical?.rationale ??
      annotation?.key_message ??
      "Selected because it contributes to the Republic-shift argument with sufficient evidence.",
    quoteText: critical?.quote_text ?? firstSentence(article.summary),
    relevanceScore: critical?.relevance_score ?? 0,
    strengthLabel: critical?.strength_label ?? "weak",
    quoteSource: critical?.quote_source ?? "summary_sentence",
    includeInStory: critical?.include_in_story ?? false,
  };
}

function useLazyCount(total: number, step: number) {
  const [visibleCount, setVisibleCount] = useState(Math.min(step, total));
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setVisibleCount(Math.min(step, total));
  }, [total, step]);

  useEffect(() => {
    if (!sentinelRef.current) {
      return;
    }
    if (visibleCount >= total) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (!entry?.isIntersecting) {
          return;
        }
        setVisibleCount((prev) => Math.min(prev + step, total));
      },
      {
        root: null,
        rootMargin: "420px 0px",
        threshold: 0.01,
      }
    );

    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [visibleCount, total, step]);

  return { visibleCount, sentinelRef };
}

function yearBand(records: NarrativeRecord[]): string {
  if (records.length === 0) {
    return "";
  }
  const years = records.map((record) => record.year);
  return `${Math.min(...years)}-${Math.max(...years)}`;
}

function EvidenceCard({ record }: { record: NarrativeRecord }) {
  const [isFlipped, setIsFlipped] = useState(false);

  return (
    <article className={`narrativeEvidenceCard ${isFlipped ? "isFlipped" : ""}`}>
      <div className="narrativeFlipInner">
        <section className="narrativeFlipFace narrativeFlipFront">
          <header className="narrativeEvidenceHead">
            <p className="narrativeEvidenceDate">{formatDate(record.dateIso)}</p>
            <p className="narrativeEvidenceSource">{record.publication}</p>
            <button
              type="button"
              className="narrativeFlipIconButton"
              onClick={() => setIsFlipped(true)}
              aria-label={`Show strict analysis for ${record.title}`}
              title="Show strict analysis"
            >
              <span className="narrativeFlipIcon" aria-hidden="true" />
            </button>
          </header>
          <h3 className="narrativeEvidenceTitle">
            {record.url ? (
              <a href={record.url} target="_blank" rel="noreferrer">
                {record.title}
              </a>
            ) : (
              record.title
            )}
          </h3>
          <p className="narrativeSummary">
            <strong>Summary:</strong> {record.shortSummary}
          </p>
          <p className="narrativeTakeaway">
            <strong>Takeaway:</strong> {record.takeaway}
          </p>
          <blockquote className="narrativeQuote">"{record.quoteText}"</blockquote>
          <div className="narrativeThemeRow">
            {record.themes.length > 0 ? (
              record.themes.map((theme) => (
                <span key={`${record.id}-${theme}`} className="narrativeThemeChip">
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
            <p className="narrativeEvidenceDate">{formatDate(record.dateIso)}</p>
            <p className="narrativeEvidenceSource">Critical evidence</p>
            <button
              type="button"
              className="narrativeFlipIconButton"
              onClick={() => setIsFlipped(false)}
              aria-label={`Return to qualitative view for ${record.title}`}
              title="Back to qualitative view"
            >
              <span className="narrativeFlipIcon" aria-hidden="true" />
            </button>
          </header>
          <p className="narrativeConnection">
            <strong>Phase connection:</strong> {record.connection}
          </p>
          <p className="narrativeKeyMessage">
            <strong>Selection rationale:</strong> {record.rationale}
          </p>
          <p className="narrativeEvidenceScore">
            Strength: <strong>{record.strengthLabel}</strong> | Relevance score:{" "}
            <strong>{record.relevanceScore.toFixed(1)}</strong> | Quote source:{" "}
            <strong>{record.quoteSource}</strong>
          </p>
        </section>
      </div>
    </article>
  );
}

export function RepublicShiftNarrative({
  articles,
  generatedAtUtc,
}: {
  articles: RawArticleRecord[];
  generatedAtUtc: string;
}) {
  const records = useMemo(() => {
    return articles
      .filter((article) => article.status !== "draft")
      .map(toNarrativeRecord)
      .sort((a, b) => a.dateIso.localeCompare(b.dateIso) || a.title.localeCompare(b.title));
  }, [articles]);

  const curated = useMemo(
    () => records.filter((record) => record.includeInStory),
    [records]
  );
  const sourceRows = curated.length > 0 ? curated : records;

  const phaseOne = useMemo(
    () => sourceRows.filter((record) => record.phase === "before"),
    [sourceRows]
  );
  const phaseTwo = useMemo(
    () => sourceRows.filter((record) => record.phase === "after"),
    [sourceRows]
  );

  const phaseOneLazy = useLazyCount(phaseOne.length, CHUNK_SIZE);
  const phaseTwoLazy = useLazyCount(phaseTwo.length, CHUNK_SIZE);

  const visiblePhaseOne = phaseOne.slice(0, phaseOneLazy.visibleCount);
  const visiblePhaseTwo = phaseTwo.slice(0, phaseTwoLazy.visibleCount);

  return (
    <main className="narrativePage">
      <section className="narrativeHero">
        <p className="narrativeKicker">Deep Analysis Article</p>
        <h1>The Republic Shift</h1>
        <p className="narrativeLead">
          From the death and mourning of the First Republic to the emergence of a messy,
          improvisational Second Republic.
        </p>
        <p className="narrativeMeta">
          Milestone year: <strong>{REPUBLIC_MILESTONE_YEAR}</strong> | Corpus rows used:{" "}
          <strong>{sourceRows.length}</strong> | Generated from archive:{" "}
          <strong>{generatedAtUtc}</strong>
        </p>
        <p className="narrativeNote">
          This narrative uses archive summaries and shift annotations as evidence quotes. Once full
          article text ingestion is complete, quote blocks can be upgraded to direct article
          excerpts.
        </p>
        <Link href="/" className="narrativeBackLink">
          Back to Shiv Archive
        </Link>
      </section>

      <section className="narrativeStory">
        <article className="narrativeSectionCard">
          <h2>1. What the First Republic held together</h2>
          <p>
            In Phase 1, Visvanathan&apos;s columns repeatedly stress institutions, constitutional
            language, citizenship, and ethical public reasoning. The pattern suggests a normative
            frame where democratic life still expects institutional accountability, though under
            increasing strain.
          </p>
        </article>
        <article className="narrativeSectionCard">
          <h2>2. The fracture and the transition</h2>
          <p>
            Across late Phase 1 and into the milestone period, the archive shifts from policy
            critique to concerns about democratic imagination, violence, and epistemic closure. The
            recurring diagnosis is that formal mechanisms survive, but civic meaning becomes thin.
          </p>
        </article>
        <article className="narrativeSectionCard">
          <h2>3. The second republic vocabulary</h2>
          <p>
            Phase 2 foregrounds improvisational politics: knowledge panchayats, embodied civic
            action, ecological survival, and moral imagination. Instead of returning to old
            institutional certainty, the writing maps contested, plural forms of democratic
            practice.
          </p>
        </article>
      </section>

      <section className="narrativeSplit">
        <section className="narrativePhaseColumn">
          <header className="narrativePhaseHead">
            <p className="narrativePhaseLabel">Phase 1</p>
            <h2>The First Republic and its erosion</h2>
            <p>
              {phaseOne.length} articles | years {yearBand(phaseOne)}
            </p>
          </header>
          <div className="narrativeEvidenceList">
            {visiblePhaseOne.map((record) => (
              <EvidenceCard key={`before-${record.id}`} record={record} />
            ))}
          </div>
          <div ref={phaseOneLazy.sentinelRef} className="narrativeSentinel" />
          {phaseOneLazy.visibleCount < phaseOne.length ? (
            <p className="narrativeLoading">
              Loading more Phase 1 evidence... ({phaseOneLazy.visibleCount}/{phaseOne.length})
            </p>
          ) : null}
        </section>

        <section className="narrativePhaseColumn">
          <header className="narrativePhaseHead">
            <p className="narrativePhaseLabel">Phase 2</p>
            <h2>The Second Republic in formation</h2>
            <p>
              {phaseTwo.length} articles | years {yearBand(phaseTwo)}
            </p>
          </header>
          <div className="narrativeEvidenceList">
            {visiblePhaseTwo.map((record) => (
              <EvidenceCard key={`after-${record.id}`} record={record} />
            ))}
          </div>
          <div ref={phaseTwoLazy.sentinelRef} className="narrativeSentinel" />
          {phaseTwoLazy.visibleCount < phaseTwo.length ? (
            <p className="narrativeLoading">
              Loading more Phase 2 evidence... ({phaseTwoLazy.visibleCount}/{phaseTwo.length})
            </p>
          ) : null}
        </section>
      </section>
    </main>
  );
}
