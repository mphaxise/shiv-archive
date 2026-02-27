"use client";

import Link from "next/link";
import { useMemo } from "react";

import { RawArticleRecord } from "@/lib/types";

type LeadGroup =
  | "institutional_grammar"
  | "decay_diagnostics"
  | "democratic_urgency"
  | "new_grammar"
  | "embodied_ethics"
  | "plural_futures"
  | "cross_currents";

interface RepublicStoryRecord {
  article_uid: string;
  phase: "before" | "after";
  published_date: string;
  url: string | null;
  publication: string;
  title: string;
  summary_snippet: string;
  signal_tags: string[];
  relevance_score: number;
  strength_label: "strong" | "moderate" | "weak";
  lead_group?: string;
  argument_text?: string;
  connection_text: string;
  quote_text: string;
  include_in_story: boolean;
  rationale?: string;
}

export interface RepublicShiftStoryPayload {
  generated_at: string;
  method: string;
  version: string;
  selected_records: RepublicStoryRecord[];
}

interface NarrativeRecord {
  id: string;
  title: string;
  dateIso: string;
  url: string | null;
  publication: string;
  year: number;
  phase: "before" | "after";
  summary: string;
  takeaway: string;
  themes: string[];
  quoteText: string;
  relevanceScore: number;
  strengthLabel: "strong" | "moderate" | "weak";
  leadGroup: LeadGroup;
}

const REPUBLIC_MILESTONE_YEAR = 2024;

const PHASE_ONE_GROUPS: LeadGroup[] = [
  "institutional_grammar",
  "democratic_urgency",
  "cross_currents",
];

const PHASE_TWO_GROUPS: LeadGroup[] = [
  "new_grammar",
  "embodied_ethics",
  "plural_futures",
  "cross_currents",
];

const GROUP_TITLES: Record<LeadGroup, string> = {
  institutional_grammar: "Institutional grammar: when constitutional language loses traction",
  decay_diagnostics: "Democratic decay: institutional erosion and public thinning",
  democratic_urgency: "Democratic urgency: civil society, ethics, and public speech",
  new_grammar: "New democratic grammar: participation beyond representation",
  embodied_ethics: "Embodied ethics: everyday morality against securitised politics",
  plural_futures: "Plural futures: ecology, constitutional redesign, and shared survival",
  cross_currents: "Cross-currents: supplementary evidence shaping the transition",
};

const GROUP_LEADS: Record<LeadGroup, string> = {
  institutional_grammar:
    "These pieces read the First Republic as a constitutional grammar now stripped of social force: the terms remain, but their lived guarantees are unstable.",
  decay_diagnostics:
    "This stream tracks institutional wear and democratic desiccation as persistent structural patterns rather than temporary exceptions.",
  democratic_urgency:
    "This cluster insists that majoritarian closure is not only electoral; it is pedagogic and ethical, shrinking the civic imagination required for democracy to function.",
  new_grammar:
    "The post-2024 writing no longer seeks restoration of old institutions alone; it tests new participatory vocabularies and direct civic invention.",
  embodied_ethics:
    "In these essays, citizenship is rebuilt through moral practice, narrative language, and concrete public pedagogy rather than abstract constitutionalism alone.",
  plural_futures:
    "This line of argument relocates democracy inside ecological and civilisational limits, pushing constitutional thought toward shared planetary responsibility.",
  cross_currents:
    "These texts sit across categories but add connective tissue between institutional critique and emergent democratic alternatives.",
};

const GROUP_ARGUMENTS: Record<LeadGroup, string> = {
  institutional_grammar:
    "The article argues that constitutional language survives while institutional guarantees are weakening in practice.",
  decay_diagnostics:
    "The article argues that democratic erosion is structural and visible in everyday institutional life.",
  democratic_urgency:
    "The article argues that ethics, dissent, and civic imagination are prerequisites for democratic repair.",
  new_grammar:
    "The article argues that a contested Second Republic is being constructed through new participatory vocabularies.",
  embodied_ethics:
    "The article argues that democratic practice must move from abstraction to embodied ethics and public pedagogy.",
  plural_futures:
    "The article argues that democratic futures require ecological responsibility and plural knowledge systems.",
  cross_currents:
    "The article argues that democratic renewal depends on connecting institutional critique with civic invention.",
};

function normalizeText(text: string | null | undefined): string {
  return (text ?? "").replace(/\s+/g, " ").trim();
}

function sentenceKey(text: string): string {
  return normalizeText(text)
    .toLowerCase()
    .replace(/[.!?]+$/g, "");
}

function sameSentence(a: string, b: string): boolean {
  return sentenceKey(a) !== "" && sentenceKey(a) === sentenceKey(b);
}

function isPlaceholderSummary(text: string): boolean {
  const normalized = normalizeText(text);
  return /^\$[a-z0-9_-]*$/i.test(normalized);
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

function firstSentence(text: string | null): string {
  const normalized = normalizeText(text);
  if (!normalized) {
    return "Summary pending.";
  }
  const match = normalized.match(/^(.+?[.!?])(\s|$)/);
  return (match?.[1] ?? punctuate(normalized)).trim();
}

function shrink(text: string, maxChars: number): string {
  const clean = text.trim();
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

function formatDate(dateIso: string): string {
  const date = new Date(`${dateIso}T00:00:00Z`);
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function formatSignalTag(slug: string): string {
  return slug
    .split("-")
    .filter(Boolean)
    .map((word) => (word.length <= 3 ? word.toUpperCase() : `${word[0].toUpperCase()}${word.slice(1)}`))
    .join(" ");
}

function cleanConnection(value: string | undefined, phase: "before" | "after"): string {
  const fallback =
    phase === "before"
      ? "Shows how First Republic institutions and citizenship guarantees are weakening in practice."
      : "Shows how the Second Republic is being assembled through new democratic practices.";

  const raw = normalizeText(value);
  if (!raw) {
    return fallback;
  }

  const lower = raw.toLowerCase();
  if (lower.includes("interrogates constitutional-institutional grammar")) {
    return "Shows constitutional language and institutional guarantees of the First Republic losing force in practice.";
  }
  if (lower.includes("diagnoses democratic erosion")) {
    return "Shows democratic erosion as a systemic process inside First Republic institutions.";
  }
  if (lower.includes("ethics, dissent, and civic urgency")) {
    return "Shows civic and ethical response to institutional decline within the First Republic frame.";
  }
  if (lower.includes("emerging vocabularies of a contested second republic")) {
    return "Shows emerging political language and institutions through which a contested Second Republic is forming.";
  }
  if (lower.includes("embodied action, moral imagination, and public pedagogy")) {
    return "Shows a Second Republic orientation toward embodied ethics, moral imagination, and public pedagogy.";
  }
  if (lower.includes("plural knowledge and ecological survival")) {
    return "Shows how ecological survival and plural knowledge reframe democratic responsibility in the Second Republic.";
  }

  const cleaned = raw
    .replace(/^strongly linked to phase 1 because\s*/i, "")
    .replace(/^strongly linked to phase 2 because\s*/i, "")
    .replace(/^strongly linked to first republic because\s*/i, "")
    .replace(/^strongly linked to second republic because\s*/i, "");
  const sentence = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  return punctuate(sentence) || fallback;
}

function buildSummary(summarySource: string | null | undefined, connection: string): string {
  const normalized = normalizeText(summarySource);
  if (!normalized || isPlaceholderSummary(normalized)) {
    return connection;
  }
  const sentences = splitSentences(normalized);
  const first = sentences[0] ? punctuate(sentences[0]) : "";
  const second = sentences[1] ? punctuate(sentences[1]) : punctuate(connection);

  if (first && second && first.toLowerCase() !== second.toLowerCase()) {
    return `${first} ${second}`;
  }
  if (first) {
    if (!sameSentence(first, connection)) {
      return `${first} ${punctuate(connection)}`;
    }
    return first;
  }
  return punctuate(connection);
}

function parseLeadGroup(raw: string | undefined): LeadGroup {
  if (
    raw === "institutional_grammar" ||
    raw === "decay_diagnostics" ||
    raw === "democratic_urgency" ||
    raw === "new_grammar" ||
    raw === "embodied_ethics" ||
    raw === "plural_futures" ||
    raw === "cross_currents"
  ) {
    return raw;
  }
  return "cross_currents";
}

function parseLeadGroupFromRationale(raw: string | undefined): LeadGroup {
  const match = raw?.match(/lead_group=([a-z_]+)/);
  return parseLeadGroup(match?.[1]);
}

function buildTakeawaySupport(
  summarySource: string | null | undefined,
  connection: string,
  fallback: string
): string {
  const normalizedSummary = normalizeText(summarySource);
  if (normalizedSummary && !isPlaceholderSummary(normalizedSummary)) {
    const summarySentences = splitSentences(normalizedSummary).map((sentence) => punctuate(sentence));
    if (summarySentences[1]) {
      return summarySentences[1];
    }
    if (summarySentences[0]) {
      return summarySentences[0];
    }
  }

  const connectionSentence = punctuate(connection);
  if (connectionSentence) {
    return connectionSentence;
  }
  return punctuate(fallback);
}

function buildTakeaway(
  leadGroup: LeadGroup,
  connection: string,
  phase: "before" | "after",
  summarySource: string | null | undefined,
  argumentOverride?: string
): string {
  const first = punctuate(normalizeText(argumentOverride) || GROUP_ARGUMENTS[leadGroup]);
  const fallback =
    phase === "before"
      ? "This reframes republic decline as an everyday democratic problem, not a purely legal one."
      : "This recasts democratic reconstruction as civic practice rather than institutional inheritance.";
  const support = buildTakeawaySupport(summarySource, connection, fallback);
  const second = sameSentence(first, support) ? punctuate(fallback) : support;
  if (!second || sameSentence(first, second)) {
    return first;
  }
  return `${first} ${second}`.trim();
}

function yearBand(records: NarrativeRecord[]): string {
  if (records.length === 0) {
    return "";
  }
  const years = records.map((record) => record.year);
  return `${Math.min(...years)}-${Math.max(...years)}`;
}

function groupByLead(records: NarrativeRecord[]) {
  const bucket = new Map<LeadGroup, NarrativeRecord[]>();
  for (const record of records) {
    const prior = bucket.get(record.leadGroup) ?? [];
    prior.push(record);
    bucket.set(record.leadGroup, prior);
  }
  for (const [key, value] of bucket.entries()) {
    bucket.set(
      key,
      [...value].sort((a, b) => a.dateIso.localeCompare(b.dateIso) || a.title.localeCompare(b.title))
    );
  }
  return bucket;
}

function toNarrativeRecord(article: RawArticleRecord): NarrativeRecord {
  const annotation = article.shift_annotations?.republic_shift;
  const critical = article.republic_critical;
  const fallbackPhase: "before" | "after" = article.year < REPUBLIC_MILESTONE_YEAR ? "before" : "after";
  const phase = critical?.phase ?? annotation?.phase ?? fallbackPhase;
  const leadGroup = parseLeadGroupFromRationale(critical?.rationale);
  const connection = cleanConnection(critical?.connection_text ?? annotation?.connection, phase);
  const summary = buildSummary(article.summary, connection);
  const takeaway = buildTakeaway(leadGroup, connection, phase, article.summary);

  return {
    id: String(article.id),
    title: article.title,
    dateIso: article.date_iso,
    year: article.year,
    url: article.url,
    publication: article.publication,
    phase,
    summary: shrink(summary, 340),
    takeaway: shrink(takeaway, 260),
    themes: article.tags.slice(0, 3).map((tag) => tag.label),
    quoteText: critical?.quote_text ?? firstSentence(article.summary),
    relevanceScore: critical?.relevance_score ?? 0,
    strengthLabel: critical?.strength_label ?? "weak",
    leadGroup,
  };
}

function toNarrativeRecordFromStory(record: RepublicStoryRecord): NarrativeRecord {
  const phase = record.phase;
  const leadGroup = parseLeadGroup(record.lead_group);
  const connection = cleanConnection(record.connection_text, phase);
  const summary = buildSummary(record.summary_snippet, connection);
  const takeaway = buildTakeaway(
    leadGroup,
    connection,
    phase,
    record.summary_snippet,
    record.argument_text
  );
  const themes =
    record.signal_tags.length > 0
      ? record.signal_tags.map((slug) => formatSignalTag(slug))
      : ["Republic Shift"];

  return {
    id: record.article_uid,
    title: record.title,
    dateIso: record.published_date,
    year: Number(record.published_date.slice(0, 4)) || REPUBLIC_MILESTONE_YEAR,
    url: record.url,
    publication: record.publication,
    phase,
    summary: shrink(summary, 340),
    takeaway: shrink(takeaway, 260),
    themes,
    quoteText: normalizeText(record.quote_text) || record.title,
    relevanceScore: Number(record.relevance_score),
    strengthLabel: record.strength_label,
    leadGroup,
  };
}

function EvidenceEntry({
  record,
  index,
  evidenceFrame,
}: {
  record: NarrativeRecord;
  index: number;
  evidenceFrame: string;
}) {
  return (
    <article className="longformEvidenceEntry" id={`evidence-${record.id}`}>
      <p className="longformEvidenceKicker">
        {evidenceFrame} evidence {index + 1}
      </p>
      <h3 className="longformEvidenceTitle">
        {record.url ? (
          <a href={record.url} target="_blank" rel="noreferrer">
            {record.title}
          </a>
        ) : (
          record.title
        )}
      </h3>
      <p className="longformEvidenceMeta">
        {formatDate(record.dateIso)} | {record.publication} | Relevance{" "}
        <strong>{record.relevanceScore.toFixed(1)}</strong> ({record.strengthLabel})
      </p>
      <p className="longformEvidenceBody">
        <strong>Summary:</strong> {record.summary}
      </p>
      <p className="longformEvidenceBody">
        <strong>Takeaway:</strong> {record.takeaway}
      </p>
      <p className="longformEvidenceBody">
        <strong>Themes:</strong> {record.themes.join(", ")}
      </p>
      <blockquote className="longformQuote">"{record.quoteText}"</blockquote>
    </article>
  );
}

export function RepublicShiftNarrative({
  articles,
  generatedAtUtc,
  story,
}: {
  articles?: RawArticleRecord[];
  generatedAtUtc?: string;
  story?: RepublicShiftStoryPayload;
}) {
  const sourceRows = useMemo(() => {
    if (story?.selected_records?.length) {
      return story.selected_records
        .filter((record) => record.include_in_story)
        .map(toNarrativeRecordFromStory)
        .sort((a, b) => a.dateIso.localeCompare(b.dateIso) || a.title.localeCompare(b.title));
    }

    const fallbackArticles = articles ?? [];
    return fallbackArticles
      .filter(
        (article) => article.status !== "draft" && article.republic_critical?.include_in_story === true
      )
      .map(toNarrativeRecord)
      .sort((a, b) => a.dateIso.localeCompare(b.dateIso) || a.title.localeCompare(b.title));
  }, [articles, story]);

  const phaseOne = useMemo(
    () => sourceRows.filter((record) => record.phase === "before"),
    [sourceRows]
  );
  const phaseTwo = useMemo(
    () => sourceRows.filter((record) => record.phase === "after"),
    [sourceRows]
  );

  const phaseOneByGroup = useMemo(() => groupByLead(phaseOne), [phaseOne]);
  const phaseTwoByGroup = useMemo(() => groupByLead(phaseTwo), [phaseTwo]);
  const sourceNames = useMemo(
    () => Array.from(new Set(sourceRows.map((record) => record.publication))).sort(),
    [sourceRows]
  );
  const snapshotLabel = story?.generated_at ?? generatedAtUtc ?? "Unknown snapshot";

  return (
    <main className="narrativePage">
      <article className="longformArticle">
        <header className="longformHeader">
          <p className="longformKicker">Deep Analysis | Long-form Experiment</p>
          <h1>The Republic Shift: From Constitutional Grammar to a Contested Second Republic</h1>
          <p className="longformLead">
            This essay reads Shiv Visvanathan&apos;s selected public writing as a single argument
            stretched across time: the First Republic&apos;s institutional language survives, but
            its democratic guarantees thin out; a Second Republic emerges through improvised
            vocabularies of participation, ethics, ecology, and civic pedagogy.
          </p>
          <p className="longformMeta">
            Milestone year: <strong>{REPUBLIC_MILESTONE_YEAR}</strong> | Selected corpus:{" "}
            <strong>{sourceRows.length}</strong> articles ({phaseOne.length} before, {phaseTwo.length}{" "}
            after) | Archive snapshot: <strong>{snapshotLabel}</strong>
          </p>
          <Link href="/" className="narrativeBackLink">
            Back to Shiv Archive
          </Link>
        </header>

        <section className="republicContextIntro">
          <h2>How this essay defines the two republics in Shiv Visvanathan&apos;s context</h2>
          <div className="republicContextGrid">
            <article className="republicContextCard">
              <p className="republicContextLabel">First Republic</p>
              <p>
                In this reading, the First Republic is the constitutional-democratic compact built
                around institutions, rights-bearing citizenship, secular plurality, public
                reasoning, and a belief that formal institutions can mediate conflict. Shiv&apos;s
                critique is not that this world never existed, but that its grammar is thinning:
                institutions remain visible while civic guarantees become fragile.
              </p>
            </article>
            <article className="republicContextCard">
              <p className="republicContextLabel">Second Republic</p>
              <p>
                The Second Republic is not a legal replacement constitution. It is a sociological
                and political condition: majoritarian, digital, improvisational, and deeply
                contested. Shiv&apos;s response is to build new democratic vocabularies inside this
                condition through knowledge panchayats, everyday ethics, ecological
                responsibility, and a more participatory form of citizenship.
              </p>
            </article>
          </div>
        </section>

        <section className="longformSection">
          <h2>Method and Scope</h2>
          <p>
            The analysis uses a strict curated Republic-shift evidence set and organizes it into
            a before/after narrative around the 2024 milestone. The aim is to test whether
            repeated concerns, examples, and conceptual moves accumulate into a historically
            legible shift.
          </p>
          <p>
            Pre-2024 writing is treated as First Republic evidence: constitutional assumptions are
            still invoked, even while their social force is being hollowed out. From 2024 onward,
            the corpus shifts into Second Republic evidence: attempts to rebuild democracy through
            participation, ethics, and ecological constitutionalism.
          </p>
          <ul className="longformStatList">
            <li>First Republic evidence range: {yearBand(phaseOne)}</li>
            <li>Second Republic evidence range: {yearBand(phaseTwo)}</li>
            <li>Primary sources represented: {sourceNames.join(", ")}</li>
          </ul>
        </section>

        <section className="longformSection">
          <h2>I. First Republic evidence (pre-2024): slow erosion of democratic guarantees</h2>
          <p>
            The pre-2024 argument is not nostalgia for a pure past. It is a diagnosis of
            democratic desiccation. Citizenship becomes precarious, institutions become
            performative, and constitutional language remains publicly available but politically
            unenforced. Repeatedly, the writing asks whether democracy can still be lived when it
            is reduced to procedure, numbers, and security.
          </p>
          {PHASE_ONE_GROUPS.map((group) => {
            const groupRows = phaseOneByGroup.get(group) ?? [];
            if (groupRows.length === 0) {
              return null;
            }
            return (
              <section key={`before-${group}`} className="longformThemeBlock">
                <aside className="longformConnectorPanel">
                  <p className="longformConnectorLabel">Argument lens</p>
                  <h3>{GROUP_TITLES[group]}</h3>
                  <p className="longformConnectorText">{GROUP_LEADS[group]}</p>
                  <p className="longformConnectorMeta">
                    First Republic evidence stream | {groupRows.length} articles
                  </p>
                </aside>
                <div className="longformEvidenceStream">
                  {groupRows.map((record, index) => (
                    <EvidenceEntry
                      key={`before-${group}-${record.id}`}
                      record={record}
                      index={index}
                      evidenceFrame="First Republic"
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </section>

        <section className="longformSection">
          <h2>II. 2024 as hinge: mourning and re-composition</h2>
          <p>
            The transition around 2024 is not framed as a clean rupture. The writing simultaneously
            mourns a collapsing institutional world and proposes alternative civic infrastructures.
            This is why the shift is best read as layered: constitutional formalism is neither
            fully rejected nor sufficient; it is re-specified through knowledge panchayats, direct
            participation, and expanded notions of responsibility.
          </p>
        </section>

        <section className="longformSection">
          <h2>III. Second Republic evidence (2024 onward): contested democratic construction</h2>
          <p>
            The post-2024 essays foreground a politics of construction rather than complaint alone.
            Citizenship must be placed back inside democracy as practice, not token membership;
            democratic speech must become intelligible in everyday language; and constitutional
            reasoning must stretch beyond nation-state security to include ecological limits and
            shared futures.
          </p>
          {PHASE_TWO_GROUPS.map((group) => {
            const groupRows = phaseTwoByGroup.get(group) ?? [];
            if (groupRows.length === 0) {
              return null;
            }
            return (
              <section key={`after-${group}`} className="longformThemeBlock">
                <aside className="longformConnectorPanel">
                  <p className="longformConnectorLabel">Argument lens</p>
                  <h3>{GROUP_TITLES[group]}</h3>
                  <p className="longformConnectorText">{GROUP_LEADS[group]}</p>
                  <p className="longformConnectorMeta">
                    Second Republic evidence stream | {groupRows.length} articles
                  </p>
                </aside>
                <div className="longformEvidenceStream">
                  {groupRows.map((record, index) => (
                    <EvidenceEntry
                      key={`after-${group}-${record.id}`}
                      record={record}
                      index={index}
                      evidenceFrame="Second Republic"
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </section>

        <section className="longformSection">
          <h2>IV. What this shift entails</h2>
          <ol className="longformInferenceList">
            <li>
              The First Republic&apos;s vocabulary of institutions, rights, and representation remains
              necessary but is no longer sufficient as a democratic operating system.
            </li>
            <li>
              The Second Republic is being argued into existence through practices: knowledge
              panchayats, civic storytelling, ethical pedagogy, and expanded constitutional
              responsibility.
            </li>
            <li>
              Democracy in this archive is treated as future-facing craft, not electoral closure.
              The core question shifts from &quot;Who wins?&quot; to &quot;What forms of life can still be
              made democratic?&quot;
            </li>
          </ol>
        </section>
      </article>
    </main>
  );
}
