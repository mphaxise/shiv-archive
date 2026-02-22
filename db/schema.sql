PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    base_url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY,
    publication_id INTEGER NOT NULL REFERENCES publications(id) ON DELETE RESTRICT,
    external_id TEXT,
    canonical_url TEXT NOT NULL UNIQUE,
    section TEXT NOT NULL DEFAULT 'Opinion',
    title TEXT NOT NULL,
    normalized_title TEXT,
    author_name TEXT NOT NULL DEFAULT 'Shiv Visvanathan',
    published_at TEXT NOT NULL,
    reading_minutes INTEGER,
    year INTEGER GENERATED ALWAYS AS (CAST(strftime('%Y', published_at) AS INTEGER)) VIRTUAL,
    summary TEXT,
    tone TEXT,
    summary_method TEXT NOT NULL DEFAULT 'manual',
    summary_model TEXT,
    retrieval_method TEXT NOT NULL DEFAULT 'manual_screenshot',
    source_capture_date TEXT,
    provenance_note TEXT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'verified', 'published')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_year ON articles(year);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_title_date ON articles(normalized_title, published_at);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL CHECK (domain IN ('sociology', 'policy', 'anthropology', 'cross_cutting')),
    description TEXT,
    is_seed INTEGER NOT NULL DEFAULT 0 CHECK (is_seed IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tags_domain ON tags(domain);

CREATE TABLE IF NOT EXISTS article_tags (
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    confidence REAL NOT NULL DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    method TEXT NOT NULL DEFAULT 'manual' CHECK (method IN ('manual', 'keyword', 'llm_map', 'hybrid')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (article_id, tag_id, method)
);

CREATE INDEX IF NOT EXISTS idx_article_tags_tag ON article_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_article_tags_article ON article_tags(article_id);

CREATE TABLE IF NOT EXISTS source_assets (
    id INTEGER PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id) ON DELETE SET NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('screenshot', 'pdf', 'html', 'notes')),
    file_path TEXT NOT NULL,
    sha256 TEXT,
    capture_date TEXT,
    ocr_text TEXT,
    ocr_confidence REAL CHECK (ocr_confidence >= 0.0 AND ocr_confidence <= 1.0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_source_assets_article ON source_assets(article_id);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    source_type TEXT NOT NULL CHECK (source_type IN ('screenshot', 'url_list', 'manual_form')),
    input_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS article_notes (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    note_type TEXT NOT NULL CHECK (note_type IN ('qa', 'methodology', 'context')),
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
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
ON shift_annotations(article_id, shift_id, annotation_version, input_fingerprint);

CREATE INDEX IF NOT EXISTS idx_shift_annotations_lookup
ON shift_annotations(article_id, shift_id, generated_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_shift_annotations_run_uid
ON shift_annotations(run_uid);

INSERT OR IGNORE INTO publications (id, name, base_url)
VALUES (1, 'The New Indian Express', 'https://www.newindianexpress.com');
