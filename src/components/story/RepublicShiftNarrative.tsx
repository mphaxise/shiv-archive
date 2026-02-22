"use client";

import Link from "next/link";
import { useMemo } from "react";

import { RawArticleRecord } from "@/lib/types";

interface NarrativeRecord {
  id: string;
  title: string;
  dateIso: string;
  url: string | null;
  publication: string;
  year: number;
  phase: "before" | "after";
  summary: string;
  keyMessage: string;
  connection: string;
  quoteText: string;
  relevanceScore: number;
  strengthLabel: "strong" | "moderate" | "weak";
  leadGroup:
    | "institutional_grammar"
    | "democratic_urgency"
    | "new_grammar"
    | "embodied_ethics"
    | "plural_futures"
    | "cross_currents";
}

const REPUBLIC_MILESTONE_YEAR = 2024;

const PHASE_ONE_GROUPS: NarrativeRecord["leadGroup"][] = [
  "institutional_grammar",
  "democratic_urgency",
  "cross_currents",
];

const PHASE_TWO_GROUPS: NarrativeRecord["leadGroup"][] = [
  "new_grammar",
  "embodied_ethics",
  "plural_futures",
  "cross_currents",
];

const GROUP_TITLES: Record<NarrativeRecord["leadGroup"], string> = {
  institutional_grammar: "Institutional grammar: when constitutional language loses traction",
  democratic_urgency: "Democratic urgency: civil society, ethics, and public speech",
  new_grammar: "New democratic grammar: participation beyond representation",
  embodied_ethics: "Embodied ethics: everyday morality against securitised politics",
  plural_futures: "Plural futures: ecology, constitutional redesign, and shared survival",
  cross_currents: "Cross-currents: supplementary evidence shaping the transition",
};

const GROUP_LEADS: Record<NarrativeRecord["leadGroup"], string> = {
  institutional_grammar:
    "These pieces read the First Republic as a constitutional grammar now stripped of social force: the terms remain, but their lived guarantees are unstable.",
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

function cleanKeyMessage(value: string | undefined): string {
  if (!value) {
    return "";
  }
  return value
    .replace(/\s*(First Republic signal:|Second Republic signal:).*/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function cleanConnection(
  value: string | undefined,
  phase: "before" | "after"
): string {
  const fallback =
    phase === "before"
      ? "Shows how First Republic institutions and citizenship guarantees are weakening in practice."
      : "Shows how the Second Republic is being assembled through new democratic practices.";

  const raw = (value ?? "").replace(/\s+/g, " ").trim();
  if (!raw) {
    return fallback;
  }

  const lower = raw.toLowerCase();
  if (lower.includes("interrogates constitutional-institutional grammar")) {
    return "Shows constitutional language and institutional guarantees of the First Republic losing force in practice.";
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
  return sentence || fallback;
}

function parseLeadGroup(raw: string | undefined): NarrativeRecord["leadGroup"] {
  const match = raw?.match(/lead_group=([a-z_]+)/);
  const lead = match?.[1] as NarrativeRecord["leadGroup"] | undefined;
  if (!lead) {
    return "cross_currents";
  }
  if (
    lead === "institutional_grammar" ||
    lead === "democratic_urgency" ||
    lead === "new_grammar" ||
    lead === "embodied_ethics" ||
    lead === "plural_futures" ||
    lead === "cross_currents"
  ) {
    return lead;
  }
  return "cross_currents";
}

function yearBand(records: NarrativeRecord[]): string {
  if (records.length === 0) {
    return "";
  }
  const years = records.map((record) => record.year);
  return `${Math.min(...years)}-${Math.max(...years)}`;
}

function groupByLead(records: NarrativeRecord[]) {
  const bucket = new Map<NarrativeRecord["leadGroup"], NarrativeRecord[]>();
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
  const summarySentence = firstSentence(article.summary);
  const cleanedMessage = cleanKeyMessage(annotation?.key_message);

  return {
    id: String(article.id),
    title: article.title,
    dateIso: article.date_iso,
    year: article.year,
    url: article.url,
    publication: article.publication,
    phase,
    summary: shrink(summarySentence, 230),
    keyMessage: cleanedMessage || summarySentence,
    connection: cleanConnection(
      critical?.connection_text ?? annotation?.connection,
      phase
    ),
    quoteText: critical?.quote_text ?? summarySentence,
    relevanceScore: critical?.relevance_score ?? 0,
    strengthLabel: critical?.strength_label ?? "weak",
    leadGroup: parseLeadGroup(critical?.rationale),
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
        <strong>Key message:</strong> {record.keyMessage}
      </p>
      <p className="longformEvidenceBody">
        <strong>Republic linkage:</strong> {record.connection}
      </p>
      <blockquote className="longformQuote">"{record.quoteText}"</blockquote>
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
  const sourceRows = useMemo(() => {
    return articles
      .filter(
        (article) => article.status !== "draft" && article.republic_critical?.include_in_story === true
      )
      .map(toNarrativeRecord)
      .sort((a, b) => a.dateIso.localeCompare(b.dateIso) || a.title.localeCompare(b.title));
  }, [articles]);

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
            after) | Archive snapshot: <strong>{generatedAtUtc}</strong>
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
            The analysis uses only the curated Republic-shift evidence set already marked as
            narratively strong in the archive pipeline. The aim is not to force every article into
            one thesis, but to test whether repeated concerns, examples, and conceptual moves
            accumulate into a historically legible shift.
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
            <li>Primary sources represented: Scroll.in, Outlook India, The New Indian Express, EPW</li>
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
          <p>
            Real-world stress tests are concrete: Kashmir&apos;s human shield episode, CAA-era
            protests, majoritarian narrowing of minority status, and the public silence around
            civic injury. The First Republic appears here less as a settled achievement and more as
            a fading grammar that no longer compels institutions to act democratically.
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
          <p>
            The result is a more unstable but more inventive democratic horizon. The emerging
            Second Republic is not a doctrinal replacement text. It is an argument for continuous
            democratic work in which ethics, pedagogy, and ecological survival become central
            constitutional concerns.
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
          <p>
            The external reference points are deliberate: Gaza, Trumpian majoritarianism, and South
            Asian peace imaginaries are used as comparative warnings and pedagogic prompts. The
            writing treats these not as foreign episodes but as mirrors for Indian democratic
            design.
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
          <p>
            On this reading, the Republic Shift is not a move from order to chaos. It is a move
            from inherited certainty to deliberate democratic invention under conditions of moral,
            ecological, and institutional stress.
          </p>
        </section>
      </article>
    </main>
  );
}
