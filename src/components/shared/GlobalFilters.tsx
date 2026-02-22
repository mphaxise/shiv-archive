"use client";

import { ChangeEvent, KeyboardEvent, useMemo, useState } from "react";

import { SHIFT_DEFINITIONS } from "@/lib/shift-definitions";
import { DatasetMetadata } from "@/lib/types";
import { useResearchState } from "@/state/research-state";

interface SearchSuggestion {
  label: string;
  query: string;
  group: "tag" | "theme" | "tone" | "section" | "source";
  priority: number;
  aliases: string[];
}

const STATIC_THEME_SUGGESTIONS: Array<Omit<SearchSuggestion, "priority">> = [
  {
    label: "Democracy",
    query: "democracy",
    group: "theme",
    aliases: ["citizen", "citizenship", "republic", "public sphere"],
  },
  {
    label: "Ecology",
    query: "ecology",
    group: "theme",
    aliases: ["anthropocene", "ecocide", "environment", "nature", "aravallis"],
  },
  {
    label: "Science",
    query: "science",
    group: "theme",
    aliases: ["knowledge", "expert", "innovation", "university", "big science"],
  },
  {
    label: "Politics",
    query: "politics",
    group: "theme",
    aliases: ["dissent", "civil society", "satyagraha", "yatra", "nationalism"],
  },
  {
    label: "Ethics",
    query: "ethics",
    group: "theme",
    aliases: ["morality", "everyday ethics", "conscience"],
  },
];

function normalizeProbe(value: string): string {
  return value.trim().toLowerCase();
}

function titleCase(value: string): string {
  return value
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}

function upsertSuggestion(
  bucket: Map<string, SearchSuggestion>,
  incoming: SearchSuggestion
): void {
  const key = normalizeProbe(incoming.query);
  if (!key) {
    return;
  }

  const existing = bucket.get(key);
  if (!existing) {
    bucket.set(key, incoming);
    return;
  }

  const mergedAliases = new Set<string>([
    ...existing.aliases.map((alias) => normalizeProbe(alias)),
    ...incoming.aliases.map((alias) => normalizeProbe(alias)),
  ]);

  bucket.set(key, {
    ...existing,
    label: existing.priority >= incoming.priority ? existing.label : incoming.label,
    group: existing.priority >= incoming.priority ? existing.group : incoming.group,
    priority: Math.max(existing.priority, incoming.priority),
    aliases: Array.from(mergedAliases).filter(Boolean),
  });
}

function buildSuggestionPool(metadata: DatasetMetadata): SearchSuggestion[] {
  const bucket = new Map<string, SearchSuggestion>();

  for (const tag of metadata.tags.slice(0, 35)) {
    upsertSuggestion(bucket, {
      label: tag.label,
      query: tag.label,
      group: "tag",
      priority: 200 + tag.count,
      aliases: [tag.slug, tag.slug.replace(/-/g, " "), tag.domain],
    });
  }

  for (const tone of metadata.tones) {
    upsertSuggestion(bucket, {
      label: titleCase(tone),
      query: tone,
      group: "tone",
      priority: 130,
      aliases: [],
    });
  }

  for (const section of metadata.sections) {
    upsertSuggestion(bucket, {
      label: section,
      query: section,
      group: "section",
      priority: 120,
      aliases: [section.toLowerCase()],
    });
  }

  for (const publication of metadata.publications ?? []) {
    upsertSuggestion(bucket, {
      label: publication.name,
      query: publication.name,
      group: "source",
      priority: 110 + publication.count,
      aliases: [publication.name.replace(/^the\s+/i, "")],
    });
  }

  for (const theme of STATIC_THEME_SUGGESTIONS) {
    upsertSuggestion(bucket, {
      ...theme,
      priority: 150,
    });
  }

  const shiftKeywords = Object.values(SHIFT_DEFINITIONS).flatMap((shift) => shift.keywords);
  for (const keyword of shiftKeywords) {
    const query = keyword.trim();
    if (!query || query.length < 4) {
      continue;
    }
    upsertSuggestion(bucket, {
      label: titleCase(query),
      query,
      group: "theme",
      priority: 100,
      aliases: [],
    });
  }

  return Array.from(bucket.values()).sort(
    (a, b) => b.priority - a.priority || a.label.localeCompare(b.label)
  );
}

function matchesSuggestion(suggestion: SearchSuggestion, query: string): boolean {
  if (!query) {
    return true;
  }
  const probe = normalizeProbe(query);
  const fields = [
    normalizeProbe(suggestion.label),
    normalizeProbe(suggestion.query),
    ...suggestion.aliases.map((alias) => normalizeProbe(alias)),
  ];
  return fields.some((field) => field.includes(probe));
}

function rankSuggestion(suggestion: SearchSuggestion, query: string): number {
  const probe = normalizeProbe(query);
  const queryNorm = normalizeProbe(suggestion.query);
  const labelNorm = normalizeProbe(suggestion.label);
  let score = suggestion.priority;
  if (!probe) {
    return score;
  }
  if (queryNorm === probe || labelNorm === probe) {
    score += 500;
  } else if (queryNorm.startsWith(probe) || labelNorm.startsWith(probe)) {
    score += 300;
  } else if (queryNorm.includes(probe) || labelNorm.includes(probe)) {
    score += 120;
  }
  if (suggestion.group === "tag") {
    score += 40;
  }
  return score;
}

function groupLabel(group: SearchSuggestion["group"]): string {
  switch (group) {
    case "tag":
      return "Tag";
    case "tone":
      return "Tone";
    case "section":
      return "Section";
    case "source":
      return "Source";
    default:
      return "Theme";
  }
}

export function GlobalFilters({ metadata }: { metadata: DatasetMetadata }) {
  const { state, dispatch } = useResearchState();
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const suggestionPool = useMemo(() => buildSuggestionPool(metadata), [metadata]);
  const suggestions = useMemo(() => {
    const query = state.activeFilter.searchTerm;
    return suggestionPool
      .filter((suggestion) => matchesSuggestion(suggestion, query))
      .sort(
        (a, b) =>
          rankSuggestion(b, query) - rankSuggestion(a, query) ||
          a.label.localeCompare(b.label)
      )
      .slice(0, 8);
  }, [state.activeFilter.searchTerm, suggestionPool]);

  const hintSuggestions = useMemo(() => suggestionPool.slice(0, 6), [suggestionPool]);

  const onSearchChange = (event: ChangeEvent<HTMLInputElement>) => {
    dispatch({ type: "set-search", searchTerm: event.target.value });
    setIsOpen(true);
    setHighlightedIndex(-1);
  };

  const onYearChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    dispatch({ type: "set-year", year: value === "all" ? "all" : Number(value) });
  };

  const applySuggestion = (suggestion: SearchSuggestion) => {
    dispatch({ type: "set-search", searchTerm: suggestion.query });
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const onSearchKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (!suggestions.length) {
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setIsOpen(true);
      setHighlightedIndex((prev) => (prev >= suggestions.length - 1 ? 0 : prev + 1));
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setIsOpen(true);
      setHighlightedIndex((prev) => (prev <= 0 ? suggestions.length - 1 : prev - 1));
      return;
    }

    if (event.key === "Enter" && highlightedIndex >= 0) {
      event.preventDefault();
      applySuggestion(suggestions[highlightedIndex]);
      return;
    }

    if (event.key === "Escape") {
      setIsOpen(false);
      setHighlightedIndex(-1);
    }
  };

  return (
    <section className="filterBar">
      <label className="filterControl searchControl">
        <span>Search</span>
        <div className="searchInputWrap">
          <input
            type="search"
            value={state.activeFilter.searchTerm}
            onChange={onSearchChange}
            onFocus={() => setIsOpen(true)}
            onBlur={() => {
              window.setTimeout(() => {
                setIsOpen(false);
                setHighlightedIndex(-1);
              }, 120);
            }}
            onKeyDown={onSearchKeyDown}
            placeholder="Search themes, tags, summaries..."
            aria-label="Search by tag, theme, summary, source, or tone"
            aria-expanded={isOpen}
            aria-autocomplete="list"
          />

          {isOpen && suggestions.length > 0 ? (
            <div className="searchSuggestionPanel" role="listbox" aria-label="Search suggestions">
              {suggestions.map((suggestion, index) => (
                <button
                  key={`${suggestion.group}:${suggestion.query}`}
                  type="button"
                  className={`searchSuggestionItem${highlightedIndex === index ? " active" : ""}`}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => applySuggestion(suggestion)}
                >
                  <span className="searchSuggestionLabel">{suggestion.label}</span>
                  <span className="searchSuggestionMeta">{groupLabel(suggestion.group)}</span>
                </button>
              ))}
            </div>
          ) : null}
        </div>

        {state.activeFilter.searchTerm.trim().length === 0 ? (
          <div className="searchHintRow">
            {hintSuggestions.map((suggestion) => (
              <button
                key={`hint:${suggestion.group}:${suggestion.query}`}
                className="searchHintChip"
                type="button"
                onClick={() => applySuggestion(suggestion)}
              >
                {suggestion.query}
              </button>
            ))}
          </div>
        ) : null}
      </label>

      <label className="filterControl">
        <span>Year</span>
        <select value={state.activeFilter.year} onChange={onYearChange}>
          <option value="all">All years</option>
          {metadata.years.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
      </label>

      <button className="ghostButton" type="button" onClick={() => dispatch({ type: "reset-filters" })}>
        Reset Filters
      </button>
    </section>
  );
}
