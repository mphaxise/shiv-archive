const state = {
  search: "",
  year: "all",
  tone: "all",
  section: "all",
  source: "all",
  status: "public",
  sort: "newest",
  tag: "all",
};

let dataset = { metadata: {}, articles: [] };

const dateFmt = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

async function boot() {
  dataset = await loadData();
  hydrateMeta(dataset.metadata);
  buildFilterOptions(dataset.metadata);
  wireEvents();
  render();
}

async function loadData() {
  const response = await fetch("./data/articles.json", { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Could not load dataset: HTTP ${response.status}`);
  }
  return response.json();
}

function hydrateMeta(metadata) {
  const rangeNode = document.querySelector("#meta-range");
  const generatedNode = document.querySelector("#meta-generated");
  if (metadata.year_range && metadata.year_range.length === 2) {
    rangeNode.textContent = `Date range: ${metadata.year_range[0]}-${metadata.year_range[1]}`;
  } else {
    rangeNode.textContent = "Date range: not available";
  }
  if (metadata.generated_at_utc) {
    generatedNode.textContent = `Generated: ${metadata.generated_at_utc}`;
  } else {
    generatedNode.textContent = "Generated: unknown";
  }
}

function buildFilterOptions(metadata) {
  const years = metadata.years || [];
  const tones = metadata.tones || [];
  const sections = metadata.sections || [];

  appendOptions("#year-select", years.map((y) => [String(y), String(y)]));
  appendOptions("#tone-select", tones.map((tone) => [tone, tone]));
  appendOptions("#section-select", sections.map((sec) => [sec, sec]));
  renderTagCloud(metadata.tags || [], []);
}

function appendOptions(selector, options) {
  const select = document.querySelector(selector);
  options.forEach(([value, label]) => {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = label;
    select.appendChild(opt);
  });
}

function wireEvents() {
  document.querySelector("#search-input").addEventListener("input", (event) => {
    state.search = event.target.value.trim().toLowerCase();
    render();
  });

  document.querySelector("#year-select").addEventListener("change", (event) => {
    state.year = event.target.value;
    render();
  });

  document.querySelector("#tone-select").addEventListener("change", (event) => {
    state.tone = event.target.value;
    render();
  });

  document.querySelector("#section-select").addEventListener("change", (event) => {
    state.section = event.target.value;
    render();
  });

  document.querySelector("#source-select").addEventListener("change", (event) => {
    state.source = event.target.value;
    render();
  });

  document.querySelector("#status-select").addEventListener("change", (event) => {
    state.status = event.target.value;
    render();
  });

  document.querySelector("#sort-select").addEventListener("change", (event) => {
    state.sort = event.target.value;
    render();
  });

  document.querySelector("#clear-tag-btn").addEventListener("click", () => {
    state.tag = "all";
    render();
  });
}

function render() {
  const filtered = applyFilters(dataset.articles || []);
  const sorted = applySort(filtered);
  renderStats(sorted);
  renderTagCloud(buildTagSummary(sorted), sorted);
  renderFilterNote(sorted.length);
  renderArticles(sorted);
}

function applyFilters(records) {
  return records.filter((record) => {
    if (state.year !== "all" && String(record.year) !== state.year) {
      return false;
    }
    if (state.tone !== "all" && (record.tone || "") !== state.tone) {
      return false;
    }
    if (state.section !== "all" && (record.section || "") !== state.section) {
      return false;
    }
    if (state.source === "with_url" && !record.has_source_url) {
      return false;
    }
    if (state.status === "public" && !["verified", "published"].includes(record.status)) {
      return false;
    }
    if (state.status === "draft" && record.status !== "draft") {
      return false;
    }
    if (state.tag !== "all") {
      const hasTag = (record.tags || []).some((tag) => tag.slug === state.tag);
      if (!hasTag) {
        return false;
      }
    }
    if (!state.search) {
      return true;
    }

    const bag = [
      record.title || "",
      record.summary || "",
      record.tone || "",
      ...(record.tags || []).map((tag) => `${tag.label} ${tag.slug}`),
    ]
      .join(" ")
      .toLowerCase();
    return bag.includes(state.search);
  });
}

function applySort(records) {
  const copy = [...records];
  if (state.sort === "oldest") {
    copy.sort((a, b) => a.date_iso.localeCompare(b.date_iso));
    return copy;
  }
  if (state.sort === "title") {
    copy.sort((a, b) => a.title.localeCompare(b.title));
    return copy;
  }
  copy.sort((a, b) => b.date_iso.localeCompare(a.date_iso));
  return copy;
}

function renderStats(records) {
  const verified = records.filter((r) => r.status === "verified").length;
  const withUrl = records.filter((r) => r.has_source_url).length;
  const tagSet = new Set();
  records.forEach((r) => (r.tags || []).forEach((t) => tagSet.add(t.slug)));

  setText("#stat-visible", String(records.length));
  setText("#stat-verified", String(verified));
  setText("#stat-with-url", String(withUrl));
  setText("#stat-tagged", String(tagSet.size));
}

function buildTagSummary(records) {
  const counts = new Map();
  records.forEach((record) => {
    const seen = new Set();
    (record.tags || []).forEach((tag) => {
      if (seen.has(tag.slug)) {
        return;
      }
      seen.add(tag.slug);
      const current = counts.get(tag.slug) || { ...tag, count: 0 };
      current.count += 1;
      counts.set(tag.slug, current);
    });
  });
  return [...counts.values()].sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

function renderTagCloud(tags, records) {
  const node = document.querySelector("#tag-cloud");
  node.textContent = "";

  const top = tags.slice(0, 28);
  top.forEach((tag) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tag-chip";
    if (state.tag === tag.slug) {
      btn.classList.add("active");
    }
    btn.textContent = `${tag.label} (${tag.count})`;
    btn.addEventListener("click", () => {
      state.tag = state.tag === tag.slug ? "all" : tag.slug;
      render();
    });
    node.appendChild(btn);
  });

  document.querySelector("#clear-tag-btn").hidden = state.tag === "all";
  if (records.length === 0) {
    node.textContent = "No tags in this view.";
  }
}

function renderFilterNote(visibleCount) {
  const parts = [];
  if (state.year !== "all") parts.push(`year ${state.year}`);
  if (state.tone !== "all") parts.push(`tone ${state.tone}`);
  if (state.section !== "all") parts.push(`section ${state.section}`);
  if (state.source === "with_url") parts.push("with URL");
  if (state.status === "public") parts.push("public records");
  if (state.status === "draft") parts.push("draft records");
  if (state.tag !== "all") parts.push(`tag ${state.tag}`);
  if (state.search) parts.push(`search "${state.search}"`);

  const note = parts.length === 0 ? "Showing all records" : `Filtered by: ${parts.join(", ")}`;
  setText("#active-filter-note", `${note} (${visibleCount})`);
}

function renderArticles(records) {
  const list = document.querySelector("#article-list");
  const empty = document.querySelector("#empty-state");
  const template = document.querySelector("#article-card-template");
  list.textContent = "";

  if (records.length === 0) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  records.forEach((record, index) => {
    const node = template.content.firstElementChild.cloneNode(true);
    node.style.animationDelay = `${Math.min(index * 0.02, 0.35)}s`;

    const status = node.querySelector(".status-badge");
    status.textContent = record.status || "draft";
    if ((record.status || "").toLowerCase() !== "verified") {
      status.classList.add("draft");
    }

    const tone = node.querySelector(".tone-badge");
    if (record.tone) {
      tone.textContent = record.tone;
    } else {
      tone.remove();
    }

    const title = node.querySelector(".card-title");
    if (record.url) {
      const anchor = document.createElement("a");
      anchor.href = record.url;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = record.title;
      title.appendChild(anchor);
    } else {
      title.textContent = record.title;
    }

    const meta = [
      formatDate(record.date_iso),
      record.section || "Opinion",
      record.reading_minutes ? `${record.reading_minutes} min read` : null,
      record.summary_method ? `summary: ${record.summary_method}` : null,
    ].filter(Boolean);
    node.querySelector(".card-meta").textContent = meta.join(" | ");

    node.querySelector(".card-summary").textContent =
      record.summary || "Summary pending manual curation.";

    const tagsNode = node.querySelector(".card-tags");
    const tags = (record.tags || []).slice(0, 8);
    tags.forEach((tag) => {
      const pill = document.createElement("span");
      pill.className = "card-tag";
      pill.textContent = tag.label;
      tagsNode.appendChild(pill);
    });
    if (tags.length === 0) {
      const pill = document.createElement("span");
      pill.className = "card-tag";
      pill.textContent = "untagged";
      tagsNode.appendChild(pill);
    }

    const link = node.querySelector(".source-link");
    if (record.url) {
      link.href = record.url;
      link.textContent = "Read source";
    } else {
      link.classList.add("disabled");
      link.removeAttribute("href");
      link.textContent = "Source URL unavailable";
    }

    list.appendChild(node);
  });
}

function formatDate(value) {
  if (!value) return "Unknown date";
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return value;
  return dateFmt.format(date);
}

function setText(selector, value) {
  const node = document.querySelector(selector);
  if (node) {
    node.textContent = value;
  }
}

boot().catch((error) => {
  console.error(error);
  setText("#active-filter-note", "Could not load dataset.");
  setText("#stat-visible", "0");
});
