import Fuse from "fuse.js";

import { ShiftProjectionRecord } from "@/lib/types";

const TERM_SYNONYMS: Record<string, string[]> = {
  environment: ["ecology", "anthropocene", "ecocide", "nature", "aravallis"],
  nature: ["ecology", "anthropocene", "ecocide", "environment", "survival"],
  democracy: ["citizen", "public", "republic", "politics"],
  science: ["knowledge", "expert", "big science", "innovation", "university"],
  politics: ["dissent", "civil society", "satyagraha", "yatra", "ethics"],
};

function expandQueryTerms(rawQuery: string): string {
  const query = rawQuery.trim().toLowerCase();
  if (!query) {
    return "";
  }

  const terms = query.split(/\s+/);
  const expanded = new Set<string>(terms);
  for (const term of terms) {
    const mapped = TERM_SYNONYMS[term];
    if (!mapped) {
      continue;
    }
    for (const synonym of mapped) {
      expanded.add(synonym);
    }
  }
  return Array.from(expanded).join(" ");
}

function searchableTags(record: ShiftProjectionRecord): string[] {
  return record.analysis.tags.map((tag) => `${tag.label} ${tag.slug}`);
}

export function searchShiftRecords(
  records: ShiftProjectionRecord[],
  query: string
): ShiftProjectionRecord[] {
  const expanded = expandQueryTerms(query);
  if (!expanded) {
    return records;
  }

  const fuse = new Fuse(records, {
    includeScore: true,
    threshold: 0.35,
    ignoreLocation: true,
    keys: [
      { name: "meta.title", weight: 0.45 },
      { name: "analysis.summary", weight: 0.25 },
      { name: "analysis.tags.label", weight: 0.2 },
      { name: "analysis.tags.slug", weight: 0.1 },
    ],
  });

  const fuseResult = fuse.search(expanded).map((entry) => entry.item);
  if (fuseResult.length === 0) {
    const simple = expanded.toLowerCase();
    return records.filter((record) => {
      const bag = [
        record.meta.title,
        record.analysis.summary ?? "",
        ...searchableTags(record),
      ]
        .join(" ")
        .toLowerCase();
      return bag.includes(simple);
    });
  }
  return fuseResult;
}

