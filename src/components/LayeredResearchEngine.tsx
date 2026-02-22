"use client";

import { GlobalFilters } from "@/components/shared/GlobalFilters";
import { ViewSwitcher } from "@/components/shared/ViewSwitcher";
import { LayerHost } from "@/components/layers/LayerHost";
import { DatasetPayload } from "@/lib/types";
import { ResearchStateProvider } from "@/state/research-state";

export function LayeredResearchEngine({ dataset }: { dataset: DatasetPayload }) {
  const visibleCount = dataset.articles.filter((article) => article.status !== "draft").length;
  const yearStart = dataset.metadata.year_range[0] ?? dataset.metadata.years.at(-1) ?? "";
  const yearEnd =
    dataset.metadata.year_range[dataset.metadata.year_range.length - 1] ??
    dataset.metadata.years[0] ??
    "";
  const sourceBreakdown = (dataset.metadata.publications ?? [])
    .map((source) => `${source.name} (${source.count})`)
    .join(" | ");

  return (
    <ResearchStateProvider>
      <div className="appShell">
        <main className="workspace">
          <section className="heroPanel">
            <div className="heroCopy">
              <p className="eyebrow">Shiv Visvanathan Archive</p>
              <h1>Shiv Archive</h1>
              <p className="heroLead">
                A curated article archive of ideas, essays, and public thought by Shiv Visvanathan,
                focused on how knowledge, science, culture, and democracy shape each other in
                public life.
              </p>
              <p className="heroBody">
                This is now a multi-publication research corpus spanning major opinion venues.
                Raw article records live in a locked master database, while summaries, tags, and
                shift annotations evolve in a separate analysis database through auditable scripts.
              </p>
              <p className="heroSources">Article sources: {sourceBreakdown}</p>
              <div className="heroActions">
                <a className="heroCta" href="#research-archive">
                  Jump to Archive
                </a>
              </div>
            </div>
            <figure className="heroFigure">
              <img
                src="https://media.newindianexpress.com/newindianexpress/2024-05/455b1647-790e-48d7-b1aa-c4310948c5f6/Shiv_Visvanathan.jpg"
                alt="Shiv Visvanathan portrait"
              />
            </figure>
          </section>

          <section className="introPanel">
            <article className="introCard">
              <h3>What This Is</h3>
              <p>
                A learning-first archive that organizes Shiv Visvanathan&apos;s opinion writing into
                a searchable public corpus across The New Indian Express, Scroll.in, EPW, and
                Outlook India. The default view is a complete database of articles; the second view
                traces the Republic Shift as a layered narrative over time.
              </p>
            </article>

            <article className="introCard">
              <h3>Why It Matters</h3>
              <p>
                Visvanathan&apos;s work on cognitive justice and plurality of knowledge remains vital
                for debates on democracy, science policy, and technology. The archive helps readers
                connect recurring themes across years instead of reading pieces in isolation.
              </p>
            </article>

            <article className="introCard">
              <h3>Who Is Building It</h3>
              <p>
                Built on Sunday morning, February 22, 2026, by a former student (undergrad years
                2002-2006, then DA-IICT) using Codex and generative AI as research tools, with the
                goal of public engagement and careful curation of already published writing.
              </p>
            </article>
          </section>

          <section id="research-archive" className="workspaceHead">
            <div>
              <p className="eyebrow">Research Corpus</p>
              <h2>{dataset.metadata.dataset}</h2>
              <p className="workspaceMeta">
                {visibleCount} visible articles | {dataset.metadata.verified_count} verified | years{" "}
                {yearStart}-{yearEnd}
                {typeof dataset.metadata.full_text_count === "number"
                  ? ` | full text ${dataset.metadata.full_text_count}`
                  : ""}
                {typeof dataset.metadata.republic_curated_count === "number"
                  ? ` | republic curated ${dataset.metadata.republic_curated_count}`
                  : ""}
              </p>
            </div>
            <p className="workspaceSources">Sources: {sourceBreakdown}</p>
            <p className="workspaceNote">
              Default view: full article database. Secondary view: Republic Shift lens.
            </p>
          </section>

          <ViewSwitcher />
          <GlobalFilters metadata={dataset.metadata} />
          <LayerHost articles={dataset.articles} />
        </main>
      </div>
    </ResearchStateProvider>
  );
}
