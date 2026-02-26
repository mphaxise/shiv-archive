import Link from "next/link";

type SciencePhase = "before" | "after";

type ScienceLeadGroup =
  | "institutional_knowledge"
  | "diagnosing_closure"
  | "democratic_learning"
  | "distributed_publics"
  | "playful_science"
  | "ethics_of_knowledge"
  | "cross_currents";

interface ScienceStoryRecord {
  article_uid: string;
  phase: SciencePhase;
  published_date: string;
  url: string;
  publication: string;
  title: string;
  summary_snippet: string;
  signal_tags: string[];
  signal_count: number;
  relevance_score: number;
  strength_label: "strong" | "moderate" | "weak";
  group_hits: Record<string, number | undefined>;
  connection_text: string;
  quote_text: string;
  include_in_story: boolean;
  selection_reason: string;
}

export interface ScienceShiftStoryPayload {
  generated_at: string;
  method: string;
  version: string;
  selection_params: {
    max_per_phase: number;
    min_score: number;
    min_anchor_hits: number;
    min_group_hits: number;
    backfill_to_phase_cap: boolean;
  };
  selected_counts: {
    before: number;
    after: number;
  };
  selected_records: ScienceStoryRecord[];
}

interface NarrativeRecord extends ScienceStoryRecord {
  lead_group: ScienceLeadGroup;
}

const SCIENCE_MILESTONE_YEAR = 2023;

const PHASE_ONE_GROUPS: ScienceLeadGroup[] = [
  "institutional_knowledge",
  "diagnosing_closure",
  "democratic_learning",
  "cross_currents",
];

const PHASE_TWO_GROUPS: ScienceLeadGroup[] = [
  "distributed_publics",
  "playful_science",
  "ethics_of_knowledge",
  "cross_currents",
];

const GROUP_TITLES: Record<ScienceLeadGroup, string> = {
  institutional_knowledge:
    "Institutional knowledge: universities, experts, and the limits of formal authority",
  diagnosing_closure:
    "Diagnosing closure: bureaucratic drift, conceptual exhaustion, and policy narrowness",
  democratic_learning:
    "Democratic learning: science as commons, dialogue, and public reasoning",
  distributed_publics:
    "Distributed publics: knowledge panchayats and plural policy participation",
  playful_science:
    "Playful science: moving beyond managerial Big Science to creative public experimentation",
  ethics_of_knowledge:
    "Ethics of knowledge: conscience, care, and non-violent imaginaries of science",
  cross_currents:
    "Cross-currents: supplementary evidence connecting institutional critique and civic invention",
};

const GROUP_LEADS: Record<ScienceLeadGroup, string> = {
  institutional_knowledge:
    "These articles treat institutional science as historically important yet insufficient: the university remains central, but its public imagination has narrowed.",
  diagnosing_closure:
    "This stream shows science-policy language becoming managerial and repetitive, often unable to meet democratic complexity.",
  democratic_learning:
    "The before phase repeatedly repositions knowledge as a civic commons where dissent, dialogue, and ordinary reasoning remain essential.",
  distributed_publics:
    "The after phase expands who counts as a knower: housewives, tribal communities, activists, and non-expert publics enter policy design.",
  playful_science:
    "Science is recast as experimental public culture, where creativity and play challenge bureaucratic closure.",
  ethics_of_knowledge:
    "Knowledge politics is linked to ethics, conscience, and social repair, not only to efficiency or innovation metrics.",
  cross_currents:
    "These records bridge multiple lines of argument and help track continuity across the before/after divide.",
};

function formatDate(dateIso: string): string {
  const date = new Date(`${dateIso}T00:00:00Z`);
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function yearBand(records: NarrativeRecord[]): string {
  if (records.length === 0) {
    return "";
  }
  const years = records.map((record) => Number(record.published_date.slice(0, 4)));
  return `${Math.min(...years)}-${Math.max(...years)}`;
}

function toLeadGroup(record: ScienceStoryRecord): ScienceLeadGroup {
  const groupHits = record.group_hits ?? {};
  const candidates: ScienceLeadGroup[] =
    record.phase === "before"
      ? ["institutional_knowledge", "diagnosing_closure", "democratic_learning"]
      : ["distributed_publics", "playful_science", "ethics_of_knowledge"];

  let best: ScienceLeadGroup = "cross_currents";
  let bestScore = 0;
  for (const candidate of candidates) {
    const score = Number(groupHits[candidate] ?? 0);
    if (score > bestScore) {
      best = candidate;
      bestScore = score;
    }
  }
  return best;
}

function byDateThenTitle(a: NarrativeRecord, b: NarrativeRecord): number {
  return a.published_date.localeCompare(b.published_date) || a.title.localeCompare(b.title);
}

function groupByLead(records: NarrativeRecord[]) {
  const bucket = new Map<ScienceLeadGroup, NarrativeRecord[]>();
  for (const record of records) {
    const previous = bucket.get(record.lead_group) ?? [];
    previous.push(record);
    bucket.set(record.lead_group, previous);
  }
  for (const [key, value] of bucket.entries()) {
    bucket.set(key, [...value].sort(byDateThenTitle));
  }
  return bucket;
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
  const tags = record.signal_tags.join(", ");

  return (
    <article className="longformEvidenceEntry" id={`science-evidence-${record.article_uid}`}>
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
        {formatDate(record.published_date)} | {record.publication} | Relevance{" "}
        <strong>{record.relevance_score.toFixed(1)}</strong> ({record.strength_label})
      </p>
      <p className="longformEvidenceBody">
        <strong>Signal tags:</strong> {tags || "None"}
      </p>
      <p className="longformEvidenceBody">
        <strong>Science linkage:</strong> {record.connection_text}
      </p>
      <blockquote className="longformQuote">"{record.quote_text}"</blockquote>
    </article>
  );
}

export function ScienceShiftNarrative({ story }: { story: ScienceShiftStoryPayload }) {
  const selected = story.selected_records
    .filter((record) => record.include_in_story)
    .map((record) => ({ ...record, lead_group: toLeadGroup(record) }))
    .sort(byDateThenTitle);

  const phaseOne = selected.filter((record) => record.phase === "before");
  const phaseTwo = selected.filter((record) => record.phase === "after");
  const phaseOneByGroup = groupByLead(phaseOne);
  const phaseTwoByGroup = groupByLead(phaseTwo);

  return (
    <main className="narrativePage">
      <article className="longformArticle">
        <header className="longformHeader">
          <p className="longformKicker">Deep Analysis | Long-form Experiment</p>
          <h1>The Science Shift: From Institutional Expertise to Knowledge Commons</h1>
          <p className="longformLead">
            This essay reads the selected science-shift corpus as a transition in democratic
            knowledge politics. The earlier writing critiques expert closure and institutional
            narrowness; the later writing proposes distributed publics, playfulness, and ethical
            responsibility as conditions for living science.
          </p>
          <p className="longformMeta">
            Milestone year: <strong>{SCIENCE_MILESTONE_YEAR}</strong> | Selected corpus:{" "}
            <strong>{selected.length}</strong> articles ({phaseOne.length} before, {phaseTwo.length}{" "}
            after) | Archive snapshot: <strong>{story.generated_at}</strong>
          </p>
          <Link href="/" className="narrativeBackLink">
            Back to Shiv Archive
          </Link>
        </header>

        <section className="republicContextIntro">
          <h2>How this essay defines the two science phases</h2>
          <div className="republicContextGrid">
            <article className="republicContextCard">
              <p className="republicContextLabel">Phase 1 (Before 2023)</p>
              <p>
                Science is frequently framed through institutions, credentialed expertise, and
                policy machinery. The core anxiety is democratic: knowledge systems are visible, but
                they are increasingly detached from plural publics and dissenting imagination.
              </p>
            </article>
            <article className="republicContextCard">
              <p className="republicContextLabel">Phase 2 (2023 Onward)</p>
              <p>
                The writing turns to constructive alternatives such as knowledge panchayats,
                playful experimentation, and ethical pedagogy. Science is no longer only a domain
                of certified experts; it is treated as a civic field where multiple communities
                co-author public reasoning.
              </p>
            </article>
          </div>
        </section>

        <section className="longformSection">
          <h2>Method and scope</h2>
          <p>
            This narrative uses only the quote-backed science-shift evidence packet generated in the
            current research cycle. Selection applies strict thresholds over relevance score, anchor
            hits, and concept-group activity, then caps each phase to a fixed narrative set.
          </p>
          <ul className="longformStatList">
            <li>Method/version: {story.method}/{story.version}</li>
            <li>
              Selection gates: min score {story.selection_params.min_score}, min anchors{" "}
              {story.selection_params.min_anchor_hits}, min groups{" "}
              {story.selection_params.min_group_hits}
            </li>
            <li>
              Per-phase cap: {story.selection_params.max_per_phase} | Backfill enabled:{" "}
              {story.selection_params.backfill_to_phase_cap ? "yes" : "no"}
            </li>
            <li>Phase 1 evidence range: {yearBand(phaseOne)}</li>
            <li>Phase 2 evidence range: {yearBand(phaseTwo)}</li>
          </ul>
        </section>

        <section className="longformSection">
          <h2>I. Phase 1 evidence (pre-2023): expertise without democratic depth</h2>
          <p>
            The pre-2023 archive is not anti-science; it is anti-closure. Universities, social
            science institutions, and policy frameworks are described as necessary but increasingly
            unable to host democratic argument at scale. The repeated concern is that science becomes
            managerial while public reasoning becomes thinner.
          </p>
          {PHASE_ONE_GROUPS.map((group) => {
            const groupRows = phaseOneByGroup.get(group) ?? [];
            if (groupRows.length === 0) {
              return null;
            }
            return (
              <section key={`science-before-${group}`} className="longformThemeBlock">
                <aside className="longformConnectorPanel">
                  <p className="longformConnectorLabel">Argument lens</p>
                  <h3>{GROUP_TITLES[group]}</h3>
                  <p className="longformConnectorText">{GROUP_LEADS[group]}</p>
                  <p className="longformConnectorMeta">
                    Phase 1 science evidence stream | {groupRows.length} articles
                  </p>
                </aside>
                <div className="longformEvidenceStream">
                  {groupRows.map((record, index) => (
                    <EvidenceEntry
                      key={`science-before-${group}-${record.article_uid}`}
                      record={record}
                      index={index}
                      evidenceFrame="Phase 1"
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </section>

        <section className="longformSection">
          <h2>II. 2023 as hinge: from critique to reconstruction</h2>
          <p>
            The transition around 2023 is a change in argumentative posture. Earlier writing
            diagnoses institutional insufficiency; later writing actively prototypes alternatives.
            Knowledge panchayats, civic pedagogy, and experimental public language emerge as
            practical democratic devices, not rhetorical add-ons.
          </p>
        </section>

        <section className="longformSection">
          <h2>III. Phase 2 evidence (2023 onward): distributed and ethical knowledge publics</h2>
          <p>
            The post-2023 corpus turns to constructive work: science must become dialogic, playful,
            and ethically answerable. Ordinary language, local memory, and non-expert reasoning are
            treated as epistemic assets rather than noise.
          </p>
          {PHASE_TWO_GROUPS.map((group) => {
            const groupRows = phaseTwoByGroup.get(group) ?? [];
            if (groupRows.length === 0) {
              return null;
            }
            return (
              <section key={`science-after-${group}`} className="longformThemeBlock">
                <aside className="longformConnectorPanel">
                  <p className="longformConnectorLabel">Argument lens</p>
                  <h3>{GROUP_TITLES[group]}</h3>
                  <p className="longformConnectorText">{GROUP_LEADS[group]}</p>
                  <p className="longformConnectorMeta">
                    Phase 2 science evidence stream | {groupRows.length} articles
                  </p>
                </aside>
                <div className="longformEvidenceStream">
                  {groupRows.map((record, index) => (
                    <EvidenceEntry
                      key={`science-after-${group}-${record.article_uid}`}
                      record={record}
                      index={index}
                      evidenceFrame="Phase 2"
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </section>

        <section className="longformSection">
          <h2>IV. What this shift implies</h2>
          <ol className="longformInferenceList">
            <li>
              Science credibility now depends not only on institutional authority, but on whether
              publics can meaningfully participate in defining problems and outcomes.
            </li>
            <li>
              Knowledge democracy in this corpus is practical: panchayats, pedagogic experiments,
              and civic translation become methods of governance.
            </li>
            <li>
              The archive links scientific imagination to ethics, suggesting that future-ready
              democracy requires both epistemic plurality and moral responsibility.
            </li>
          </ol>
        </section>
      </article>
    </main>
  );
}
