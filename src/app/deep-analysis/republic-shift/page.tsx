import type { Metadata } from "next";

import { RepublicShiftNarrative } from "@/components/story/RepublicShiftNarrative";
import articlesData from "@/data/articles.json";
import { DatasetPayload } from "@/lib/types";

export const metadata: Metadata = {
  title: "Deep Analysis | Republic Shift | Shiv Archive",
  description:
    "Interactive narrative article tracing the Republic Shift across Shiv Visvanathan's archive.",
};

export default function RepublicShiftNarrativePage() {
  const dataset = articlesData as DatasetPayload;
  return (
    <RepublicShiftNarrative
      articles={dataset.articles}
      generatedAtUtc={dataset.metadata.generated_at_utc}
    />
  );
}
