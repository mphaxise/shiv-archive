"use client";

import { ChangeEvent, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { ArticleCard } from "@/components/shared/ArticleCard";
import { SHIFT_DEFINITIONS } from "@/lib/shift-definitions";
import { searchShiftRecords } from "@/lib/semantic-search";
import { RawArticleRecord, ShiftProjectionRecord } from "@/lib/types";
import { useResearchState } from "@/state/research-state";

type ChronicleSortMode =
  | "date_desc"
  | "date_asc"
  | "publication_asc"
  | "publication_desc"
  | "title_asc";

const SORT_LABELS: Record<ChronicleSortMode, string> = {
  date_desc: "Newest first",
  date_asc: "Oldest first",
  publication_asc: "Publication A-Z",
  publication_desc: "Publication Z-A",
  title_asc: "Title A-Z",
};

function alphaCompare(left: string, right: string): number {
  return left.localeCompare(right, undefined, { sensitivity: "base" });
}

function sortChronicle(
  records: ShiftProjectionRecord[],
  mode: ChronicleSortMode
): ShiftProjectionRecord[] {
  const sorted = [...records];

  sorted.sort((a, b) => {
    if (mode === "date_asc") {
      return a.meta.date_iso.localeCompare(b.meta.date_iso) || alphaCompare(a.meta.title, b.meta.title);
    }
    if (mode === "publication_asc") {
      return (
        alphaCompare(a.meta.publication, b.meta.publication) ||
        b.meta.date_iso.localeCompare(a.meta.date_iso) ||
        alphaCompare(a.meta.title, b.meta.title)
      );
    }
    if (mode === "publication_desc") {
      return (
        alphaCompare(b.meta.publication, a.meta.publication) ||
        b.meta.date_iso.localeCompare(a.meta.date_iso) ||
        alphaCompare(a.meta.title, b.meta.title)
      );
    }
    if (mode === "title_asc") {
      return (
        alphaCompare(a.meta.title, b.meta.title) ||
        b.meta.date_iso.localeCompare(a.meta.date_iso) ||
        alphaCompare(a.meta.publication, b.meta.publication)
      );
    }
    return b.meta.date_iso.localeCompare(a.meta.date_iso) || alphaCompare(a.meta.title, b.meta.title);
  });

  return sorted;
}

export function ChronicleView({ articles }: { articles: RawArticleRecord[] }) {
  const { state } = useResearchState();
  const [sortMode, setSortMode] = useState<ChronicleSortMode>("date_desc");
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
  const list = useMemo(() => sortChronicle(yearFiltered, sortMode), [yearFiltered, sortMode]);

  const onSortChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setSortMode(event.target.value as ChronicleSortMode);
  };

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
        <div className="chronicleToolbar">
          <label className="chronicleSortControl">
            <span>Sort Archive</span>
            <select value={sortMode} onChange={onSortChange} aria-label="Sort archive cards">
              <option value="date_desc">Newest first</option>
              <option value="date_asc">Oldest first</option>
              <option value="publication_asc">Publication A-Z</option>
              <option value="publication_desc">Publication Z-A</option>
              <option value="title_asc">Title A-Z</option>
            </select>
          </label>
          <p className="chronicleSortMeta">
            {list.length} articles shown | sorted by <strong>{SORT_LABELS[sortMode]}</strong>
          </p>
        </div>
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
