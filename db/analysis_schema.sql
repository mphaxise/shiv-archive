PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL CHECK (domain IN ('sociology', 'policy', 'anthropology', 'cross_cutting')),
    description TEXT,
    is_seed INTEGER NOT NULL DEFAULT 0 CHECK (is_seed IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tags_domain
ON tags(domain);

CREATE TABLE IF NOT EXISTS article_analysis (
    id INTEGER PRIMARY KEY,
    article_uid TEXT NOT NULL UNIQUE,
    summary TEXT,
    tone TEXT,
    summary_method TEXT NOT NULL DEFAULT 'manual',
    summary_model TEXT,
    analysis_status TEXT NOT NULL DEFAULT 'draft' CHECK (analysis_status IN ('draft', 'verified', 'published')),
    provenance_note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_article_analysis_status
ON article_analysis(analysis_status);

CREATE INDEX IF NOT EXISTS idx_article_analysis_tone
ON article_analysis(tone);

CREATE TABLE IF NOT EXISTS article_tags (
    article_uid TEXT NOT NULL,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    confidence REAL NOT NULL DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    method TEXT NOT NULL DEFAULT 'manual' CHECK (method IN ('manual', 'keyword', 'llm_map', 'hybrid')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (article_uid, tag_id, method)
);

CREATE INDEX IF NOT EXISTS idx_article_tags_tag
ON article_tags(tag_id);

CREATE INDEX IF NOT EXISTS idx_article_tags_article
ON article_tags(article_uid);

CREATE TABLE IF NOT EXISTS shift_annotation_runs (
    id INTEGER PRIMARY KEY,
    run_uid TEXT NOT NULL UNIQUE,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    shift_scope TEXT NOT NULL,
    annotation_method TEXT NOT NULL,
    annotation_version TEXT NOT NULL,
    inserted_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS shift_annotations (
    id INTEGER PRIMARY KEY,
    article_uid TEXT NOT NULL,
    shift_id TEXT NOT NULL CHECK (
        shift_id IN ('republic_shift', 'ecological_shift', 'science_shift', 'political_shift')
    ),
    phase TEXT NOT NULL CHECK (phase IN ('before', 'after')),
    connection_text TEXT NOT NULL,
    key_message TEXT NOT NULL,
    annotation_method TEXT NOT NULL,
    annotation_version TEXT NOT NULL,
    input_fingerprint TEXT NOT NULL,
    run_uid TEXT NOT NULL REFERENCES shift_annotation_runs(run_uid) ON DELETE RESTRICT,
    provenance_note TEXT,
    generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_shift_annotations_unique_input
ON shift_annotations(article_uid, shift_id, annotation_version, input_fingerprint);

CREATE INDEX IF NOT EXISTS idx_shift_annotations_lookup
ON shift_annotations(article_uid, shift_id, generated_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_shift_annotations_run_uid
ON shift_annotations(run_uid);
