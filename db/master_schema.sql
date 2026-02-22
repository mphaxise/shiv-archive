PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    base_url TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY,
    article_uid TEXT NOT NULL UNIQUE,
    publication_id INTEGER NOT NULL REFERENCES publications(id) ON DELETE RESTRICT,
    external_id TEXT,
    canonical_url TEXT NOT NULL,
    canonical_url_norm TEXT NOT NULL,
    section TEXT NOT NULL DEFAULT 'Opinion',
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    author_name TEXT NOT NULL DEFAULT 'Shiv Visvanathan',
    published_at TEXT NOT NULL,
    year INTEGER GENERATED ALWAYS AS (CAST(strftime('%Y', published_at) AS INTEGER)) VIRTUAL,
    reading_minutes INTEGER,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'verified', 'published')),
    retrieval_method TEXT NOT NULL DEFAULT 'manual_screenshot',
    source_capture_date TEXT,
    provenance_note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_pub_url
ON articles(publication_id, canonical_url_norm);

CREATE INDEX IF NOT EXISTS idx_articles_published_at
ON articles(published_at);

CREATE INDEX IF NOT EXISTS idx_articles_year
ON articles(year);

CREATE INDEX IF NOT EXISTS idx_articles_status
ON articles(status);

CREATE INDEX IF NOT EXISTS idx_articles_title_date
ON articles(normalized_title, published_at);

CREATE TABLE IF NOT EXISTS article_texts (
    id INTEGER PRIMARY KEY,
    article_uid TEXT NOT NULL REFERENCES articles(article_uid) ON DELETE CASCADE,
    body_text TEXT,
    text_state TEXT NOT NULL DEFAULT 'missing' CHECK (text_state IN ('missing', 'partial', 'full')),
    text_format TEXT NOT NULL DEFAULT 'plain' CHECK (text_format IN ('plain', 'html', 'markdown')),
    word_count INTEGER,
    language TEXT NOT NULL DEFAULT 'en',
    extraction_method TEXT NOT NULL DEFAULT 'not_collected',
    extraction_model TEXT,
    source_url TEXT,
    extracted_at TEXT,
    is_primary INTEGER NOT NULL DEFAULT 1 CHECK (is_primary IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_article_texts_primary
ON article_texts(article_uid, is_primary)
WHERE is_primary = 1;

CREATE INDEX IF NOT EXISTS idx_article_texts_state
ON article_texts(text_state);

CREATE TABLE IF NOT EXISTS source_assets (
    id INTEGER PRIMARY KEY,
    article_uid TEXT REFERENCES articles(article_uid) ON DELETE SET NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('screenshot', 'pdf', 'html', 'notes')),
    file_path TEXT NOT NULL,
    sha256 TEXT,
    capture_date TEXT,
    ocr_text TEXT,
    ocr_confidence REAL CHECK (ocr_confidence >= 0.0 AND ocr_confidence <= 1.0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_source_assets_article
ON source_assets(article_uid);

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
    article_uid TEXT NOT NULL REFERENCES articles(article_uid) ON DELETE CASCADE,
    note_type TEXT NOT NULL CHECK (note_type IN ('qa', 'methodology', 'context')),
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_article_notes_article
ON article_notes(article_uid);
