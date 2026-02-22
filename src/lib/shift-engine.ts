import {
  DatasetTag,
  RawArticleRecord,
  ShiftDefinition,
  ShiftProjectionRecord,
  ShiftSplitResult,
} from "@/lib/types";
import { searchShiftRecords } from "@/lib/semantic-search";

function recordCorpusText(article: RawArticleRecord): string {
  const tags = article.tags.map((tag) => `${tag.label} ${tag.slug}`).join(" ");
  return [article.title, article.summary ?? "", tags].join(" ").toLowerCase();
}

function countMatches(text: string, fragments: string[]): number {
  let score = 0;
  for (const fragment of fragments) {
    const probe = fragment.toLowerCase();
    if (text.includes(probe)) {
      score += 1;
    }
  }
  return score;
}

function preferredTagBonus(tags: DatasetTag[], preferred: string[]): number {
  const slugs = new Set(tags.map((tag) => tag.slug));
  let score = 0;
  for (const slug of preferred) {
    if (slugs.has(slug)) {
      score += 2;
    }
  }
  return score;
}

function shiftScore(article: RawArticleRecord, shift: ShiftDefinition): number {
  const text = recordCorpusText(article);
  const keywordHits = countMatches(text, shift.keywords);
  const tagBonus = preferredTagBonus(article.tags, shift.preferredTagSlugs);
  const nearMilestone = Math.abs(article.year - shift.milestoneYear) <= 2 ? 1 : 0;

  return keywordHits + tagBonus + nearMilestone;
}

function firstSentence(summary: string | null): string {
  const normalized = (summary ?? "").replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "This article captures a key transition point in the archive.";
  }
  const match = normalized.match(/^(.+?[.!?])(\s|$)/);
  return (match?.[1] ?? normalized).trim();
}

function hasAny(text: string, probes: string[]): boolean {
  return probes.some((probe) => text.includes(probe));
}

function republicConnection(article: RawArticleRecord, phase: "before" | "after"): string {
  const text = recordCorpusText(article);

  if (
    hasAny(text, [
      "constitution",
      "citizen",
      "citizenship",
      "republic",
      "democracy",
      "institution",
      "state",
    ])
  ) {
    return phase === "before"
      ? "Links to Phase 1 by showing strain in First Republic institutions and citizenship grammar."
      : "Links to Phase 2 by reframing citizenship for a contested, post-formalist Second Republic.";
  }

  if (
    hasAny(text, [
      "knowledge",
      "science",
      "university",
      "expert",
      "panchayat",
      "education",
      "innovation",
    ])
  ) {
    return phase === "before"
      ? "Links to Phase 1 by exposing how First Republic knowledge institutions narrowed democratic imagination."
      : "Links to Phase 2 by proposing distributed knowledge as a design principle for the Second Republic.";
  }

  if (
    hasAny(text, [
      "violence",
      "peace",
      "ethics",
      "morality",
      "nationalism",
      "dissent",
      "satyagraha",
      "yatra",
    ])
  ) {
    return phase === "before"
      ? "Links to Phase 1 by reading moral dissent as a response to First Republic fatigue."
      : "Links to Phase 2 by placing ethics, embodiment, and public repair at the core of new politics.";
  }

  if (hasAny(text, ["anthropocene", "ecology", "ecocide", "climate", "nature", "aravallis"])) {
    return phase === "before"
      ? "Links to Phase 1 by widening First Republic debates toward ecological citizenship and survival."
      : "Links to Phase 2 by treating ecological survival as central to the Second Republic social contract.";
  }

  return phase === "before"
    ? "Links to Phase 1 by documenting cracks between constitutional form and lived democratic experience."
    : "Links to Phase 2 by tracing emergent civic vocabularies beyond legacy institutional comfort.";
}

function buildNarrativeNote(article: RawArticleRecord, shift: ShiftDefinition, phase: "before" | "after"): string {
  if (shift.id === "republic_shift") {
    return republicConnection(article, phase);
  }
  return phase === "before" ? shift.beforeNarrative : shift.afterNarrative;
}

function buildKeyMessage(article: RawArticleRecord, shift: ShiftDefinition, phase: "before" | "after"): string {
  const base = firstSentence(article.summary);
  if (shift.id === "republic_shift") {
    const bridge =
      phase === "before"
        ? "First Republic signal: legacy institutions are under pressure."
        : "Second Republic signal: democratic practice is being re-authored.";
    return `${base} ${bridge}`;
  }
  return base;
}

function persistedAnnotationForPhase(
  article: RawArticleRecord,
  shift: ShiftDefinition,
  phase: "before" | "after"
) {
  const annotation = article.shift_annotations?.[shift.id];
  if (!annotation) {
    return null;
  }
  if (annotation.phase !== phase) {
    return null;
  }
  return annotation;
}

function toProjection(article: RawArticleRecord, shift: ShiftDefinition, score: number): ShiftProjectionRecord {
  const phase: "before" | "after" = article.year < shift.milestoneYear ? "before" : "after";
  const persisted = persistedAnnotationForPhase(article, shift, phase);

  return {
    article_id: String(article.id),
    meta: {
      year: article.year,
      title: article.title,
      date_iso: article.date_iso,
      url: article.url,
      publication: article.publication,
      section: article.section,
      reading_minutes: article.reading_minutes,
    },
    analysis: {
      summary: article.summary,
      tone: article.tone,
      tags: article.tags,
    },
    shift_context: {
      shift_id: shift.id,
      phase,
      narrative_note: persisted?.connection ?? buildNarrativeNote(article, shift, phase),
      key_message: persisted?.key_message ?? buildKeyMessage(article, shift, phase),
    },
    score,
  };
}

function compareByRelevance(a: ShiftProjectionRecord, b: ShiftProjectionRecord): number {
  if (b.score !== a.score) {
    return b.score - a.score;
  }
  if (b.meta.year !== a.meta.year) {
    return b.meta.year - a.meta.year;
  }
  return b.meta.date_iso.localeCompare(a.meta.date_iso);
}

function compareChronological(a: ShiftProjectionRecord, b: ShiftProjectionRecord): number {
  const byDate = a.meta.date_iso.localeCompare(b.meta.date_iso);
  if (byDate !== 0) {
    return byDate;
  }
  return a.meta.title.localeCompare(b.meta.title);
}

function ensureCoverage(
  allArticles: RawArticleRecord[],
  shift: ShiftDefinition,
  selected: ShiftProjectionRecord[]
): ShiftProjectionRecord[] {
  if (selected.length >= 12) {
    return selected;
  }

  const existingIds = new Set(selected.map((item) => item.article_id));
  const fallback = allArticles
    .filter((article) => !existingIds.has(String(article.id)))
    .map((article) => {
      const distance = Math.abs(article.year - shift.milestoneYear);
      const score = Math.max(0, 4 - distance);
      return toProjection(article, shift, score);
    })
    .sort(compareByRelevance)
    .slice(0, 12 - selected.length);

  return [...selected, ...fallback].sort(compareByRelevance);
}

export function buildShiftSplit(
  articles: RawArticleRecord[],
  shift: ShiftDefinition,
  searchTerm: string,
  yearFilter: "all" | number
): ShiftSplitResult {
  const projected = articles
    .map((article) => {
      const score = shiftScore(article, shift);
      return { article, score };
    })
    .filter((entry) => entry.score >= 2)
    .map((entry) => toProjection(entry.article, shift, entry.score));

  const withCoverage = ensureCoverage(articles, shift, projected);
  const searched = searchShiftRecords(withCoverage, searchTerm);
  const yearFiltered =
    yearFilter === "all"
      ? searched
      : searched.filter((record) => record.meta.year === yearFilter);

  const before = yearFiltered
    .filter((record) => record.shift_context.phase === "before")
    .sort(compareChronological);
  const after = yearFiltered
    .filter((record) => record.shift_context.phase === "after")
    .sort(compareChronological);

  return {
    definition: shift,
    before,
    after,
    total: yearFiltered.length,
  };
}
