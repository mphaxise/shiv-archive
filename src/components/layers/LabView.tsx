"use client";

import { motion } from "framer-motion";

import { buildShiftSplit } from "@/lib/shift-engine";
import { SHIFT_DEFINITIONS } from "@/lib/shift-definitions";
import { RawArticleRecord } from "@/lib/types";
import { useResearchState } from "@/state/research-state";

export function LabView({ articles }: { articles: RawArticleRecord[] }) {
  const { state } = useResearchState();
  const split = buildShiftSplit(
    articles,
    SHIFT_DEFINITIONS[state.activeShift],
    state.activeFilter.searchTerm,
    state.activeFilter.year
  );

  const beforeCount = split.before.length;
  const afterCount = split.after.length;

  return (
    <motion.section
      layout
      layoutId="layer-lab"
      className="layerPanel"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
    >
      <header className="layerHeader">
        <p className="layerKicker">Lab Lens</p>
        <h2>Experimental metrics sandbox</h2>
        <p className="layerMeta">
          Use this lane for prototype indicators before adding formal visualizations.
        </p>
      </header>

      <div className="labGrid">
        <article className="labMetric">
          <span>Departure Corpus</span>
          <strong>{beforeCount}</strong>
        </article>
        <article className="labMetric">
          <span>Arrival Corpus</span>
          <strong>{afterCount}</strong>
        </article>
        <article className="labMetric">
          <span>Shift Tension</span>
          <strong>{Math.abs(afterCount - beforeCount)}</strong>
        </article>
        <article className="labMetric">
          <span>Active Shift</span>
          <strong>{SHIFT_DEFINITIONS[state.activeShift].label}</strong>
        </article>
      </div>
    </motion.section>
  );
}

