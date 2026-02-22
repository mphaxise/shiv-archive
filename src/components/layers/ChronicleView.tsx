"use client";

import { useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { ArticleCard } from "@/components/shared/ArticleCard";
import { SHIFT_DEFINITIONS } from "@/lib/shift-definitions";
import { searchShiftRecords } from "@/lib/semantic-search";
import { RawArticleRecord, ShiftProjectionRecord } from "@/lib/types";
import { useResearchState } from "@/state/research-state";

function sortChronicle(records: ShiftProjectionRecord[]): ShiftProjectionRecord[] {
  return [...records].sort((a, b) => b.meta.date_iso.localeCompare(a.meta.date_iso));
}

export function ChronicleView({ articles }: { articles: RawArticleRecord[] }) {
  const { state } = useResearchState();
  const activeShift = SHIFT_DEFINITIONS[state.activeShift];

  const projected = useMemo<ShiftProjectionRecord[]>(
    () =>
      articles.map((article) => ({
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
          shift_id: activeShift.id,
          phase: article.year < activeShift.milestoneYear ? "before" : "after",
          narrative_note: "",
          key_message: "",
        },
        score: 0,
      })),
    [articles, activeShift.id, activeShift.milestoneYear]
  );

  const searched = searchShiftRecords(projected, state.activeFilter.searchTerm);
  const yearFiltered =
    state.activeFilter.year === "all"
      ? searched
      : searched.filter((record) => record.meta.year === state.activeFilter.year);
  const list = sortChronicle(yearFiltered);

  return (
    <motion.section
      layout
      layoutId="layer-chronicle"
      className="layerPanel"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
    >
      <header className="layerHeader">
        <p className="layerKicker">Default View</p>
        <h2>Complete database of Shiv Visvanathan articles</h2>
        <p className="layerMeta">
          Cards show title, quick summary, publish date, article type, and three key tags. Active
          shift context remains available for the Opinion Shift view: <strong>{activeShift.label}</strong>.
        </p>
      </header>

      <div className="chronicleGrid">
        <AnimatePresence mode="popLayout">
          {list.map((record) => {
            return <ArticleCard key={record.article_id} record={record} variant="archive" />;
          })}
        </AnimatePresence>
      </div>
    </motion.section>
  );
}
