import { LayeredResearchEngine } from "@/components/LayeredResearchEngine";
import articlesData from "@/data/articles.json";
import { DatasetPayload } from "@/lib/types";

export default function HomePage() {
  const dataset = articlesData as DatasetPayload;
  return <LayeredResearchEngine dataset={dataset} />;
}
