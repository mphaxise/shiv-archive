"use client";

import { motion } from "framer-motion";

import { buildShiftSplit } from "@/lib/shift-engine";
import { SHIFT_DEFINITIONS } from "@/lib/shift-definitions";
import { RawArticleRecord } from "@/lib/types";
import { useResearchState } from "@/state/research-state";

interface TagNode {
  slug: string;
  label: string;
  count: number;
}

function buildNodes(articles: ReturnType<typeof buildShiftSplit>["before"]): TagNode[] {
  const counter = new Map<string, TagNode>();
  for (const article of articles) {
    const seen = new Set<string>();
    for (const tag of article.analysis.tags) {
      if (seen.has(tag.slug)) {
        continue;
      }
      seen.add(tag.slug);
      const existing = counter.get(tag.slug);
      if (existing) {
        existing.count += 1;
      } else {
        counter.set(tag.slug, { slug: tag.slug, label: tag.label, count: 1 });
      }
    }
  }
  return [...counter.values()].sort((a, b) => b.count - a.count).slice(0, 16);
}

export function ConstellationView({ articles }: { articles: RawArticleRecord[] }) {
  const { state } = useResearchState();
  const split = buildShiftSplit(
    articles,
    SHIFT_DEFINITIONS[state.activeShift],
    state.activeFilter.searchTerm,
    state.activeFilter.year
  );

  const nodes = buildNodes([...split.before, ...split.after]);

  return (
    <motion.section
      layout
      layoutId="layer-constellation"
      className="layerPanel"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
    >
      <header className="layerHeader">
        <p className="layerKicker">Constellation Lens (Preview)</p>
        <h2>Relational theme scaffold for future D3 graph</h2>
        <p className="layerMeta">
          This module is kept hot-swappable for a future interactive graph engine.
        </p>
      </header>

      <div className="constellationField">
        {nodes.map((node, index) => (
          <motion.div
            layout
            layoutId={`tag-${node.slug}`}
            key={node.slug}
            className="constellationNode"
            style={{
              transform: `translateY(${(index % 4) * 4}px)`,
            }}
          >
            <strong>{node.label}</strong>
            <span>{node.count} linked articles</span>
          </motion.div>
        ))}
      </div>
    </motion.section>
  );
}

