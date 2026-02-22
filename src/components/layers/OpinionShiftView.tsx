"use client";

import { AnimatePresence, motion } from "framer-motion";

import { ArticleCard } from "@/components/shared/ArticleCard";
import { buildShiftSplit } from "@/lib/shift-engine";
import { SHIFT_DEFINITIONS } from "@/lib/shift-definitions";
import { RawArticleRecord } from "@/lib/types";
import { useResearchState } from "@/state/research-state";

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
      </header>

      <div className="dialecticGrid">
        <motion.section layout className="phaseColumn">
          <h3>Phase 1: The Departure</h3>
          <p className="phaseSubtitle">{shift.beforeNarrative}</p>
          <AnimatePresence mode="popLayout">
            {split.before.map((record) => (
              <ArticleCard key={record.article_id} record={record} variant="shift" />
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
              <ArticleCard key={record.article_id} record={record} variant="shift" />
            ))}
          </AnimatePresence>
        </motion.section>
      </div>
    </motion.section>
  );
}
