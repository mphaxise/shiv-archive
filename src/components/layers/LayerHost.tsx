"use client";

import { useMemo } from "react";
import { AnimatePresence } from "framer-motion";

import { ChronicleView } from "@/components/layers/ChronicleView";
import { ConstellationView } from "@/components/layers/ConstellationView";
import { LabView } from "@/components/layers/LabView";
import { OpinionShiftView } from "@/components/layers/OpinionShiftView";
import { RawArticleRecord } from "@/lib/types";
import { useResearchState } from "@/state/research-state";

export function LayerHost({ articles }: { articles: RawArticleRecord[] }) {
  const { state } = useResearchState();
  const visibleArticles = useMemo(
    () => articles.filter((article) => article.status !== "draft"),
    [articles]
  );

  return (
    <AnimatePresence mode="wait">
      {state.activeView === "opinion_shift" && (
        <OpinionShiftView key="opinion_shift" articles={visibleArticles} />
      )}
      {state.activeView === "chronicle" && <ChronicleView key="chronicle" articles={visibleArticles} />}
      {state.activeView === "constellation" && (
        <ConstellationView key="constellation" articles={visibleArticles} />
      )}
      {state.activeView === "lab" && <LabView key="lab" articles={visibleArticles} />}
    </AnimatePresence>
  );
}
