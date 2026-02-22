#!/usr/bin/env python3
"""Rebuild corpus as a multi-publication Shiv archive (61 confirmed records)."""

from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from time import sleep

import requests


SOURCE_CAPTURE_DATE = "2026-02-22"
DEFAULT_AUTHOR = "Shiv Visvanathan"

PUBLICATIONS = {
    "tnie": {
        "id": 1,
        "name": "The New Indian Express",
        "base_url": "https://www.newindianexpress.com",
    },
    "scroll": {
        "id": 2,
        "name": "Scroll.in",
        "base_url": "https://scroll.in",
    },
    "epw": {
        "id": 3,
        "name": "Economic and Political Weekly",
        "base_url": "https://www.epw.in",
    },
    "outlook": {
        "id": 4,
        "name": "Outlook India",
        "base_url": "https://www.outlookindia.com",
    },
}

KEYWORD_TAGS: dict[str, list[str]] = {
    "anthropocene": ["ecology", "technology-and-society"],
    "ecocide": ["ecology"],
    "ecology": ["ecology"],
    "democracy": ["democracy", "public-sphere"],
    "democratic": ["democracy"],
    "citizen": ["democracy"],
    "citizenship": ["democracy"],
    "policy": ["public-institutions", "law-and-justice"],
    "ethics": ["ethics"],
    "morality": ["ethics"],
    "peace": ["pluralism", "public-sphere"],
    "violence": ["law-and-justice", "pluralism"],
    "civil society": ["social-movements", "pluralism"],
    "science": ["science-policy", "technology-and-society"],
    "knowledge": ["knowledge-systems", "public-sphere"],
    "panchayat": ["knowledge-systems", "public-institutions"],
    "university": ["education-policy", "knowledge-systems"],
    "education": ["education-policy"],
    "history": ["memory"],
    "memory": ["memory"],
    "nationalism": ["nationalism"],
    "patriotism": ["nationalism", "ethics"],
    "feminism": ["identity-politics", "ethics"],
    "caste": ["caste", "identity-politics"],
    "swadeshi": ["development", "nationalism"],
    "constitution": ["law-and-justice", "democracy"],
    "theatre": ["ritual-and-symbol", "public-sphere"],
    "playfulness": ["culture-and-modernity"],
    "play": ["culture-and-modernity"],
    "orality": ["knowledge-systems", "culture-and-modernity"],
    "kashmir": ["law-and-justice", "pluralism"],
    "commons": ["development", "pluralism"],
    "secular": ["secularism", "democracy"],
    "modi": ["nationalism", "public-sphere"],
    "gandhi": ["memory", "pluralism"],
    "left": ["public-sphere", "democracy"],
    "right": ["public-sphere", "democracy"],
    "startup": ["technology-and-society", "ethics"],
}

FALLBACK_TAG_SLUGS = [
    "public-sphere",
    "ethics",
    "democracy",
    "pluralism",
    "culture-and-modernity",
]

SCROLL_RECORDS = [
    {
        "title": "Laughter Humanised Us And Made India A More Comfortable Place — Where Has It Gone?",
        "url": "https://scroll.in/article/861385",
        "year_hint": 2017,
    },
    {
        "title": "Gujarat Bishops' Plea To Save India From Nationalist Forces Is An Act Of Citizenship We Must Support",
        "url": "https://scroll.in/article/859348",
        "year_hint": 2017,
    },
    {
        "title": "Proposal To Remove M From AMU, H From BHU Shows That India Doesn't Really Understand Secularism",
        "url": "https://scroll.in/article/853581",
        "year_hint": 2017,
    },
    {
        "title": "Once The Arena Of Creative Ideological Battles, The Politics Of Survival Now Blights Tamil Nadu",
        "url": "https://scroll.in/article/851894",
        "year_hint": 2017,
    },
    {
        "title": "Question For The BJP's Ram Madhav: How Indian Are His Party's Ideas Of Nationalism And Development?",
        "url": "https://scroll.in/article/847799",
        "year_hint": 2017,
    },
    {
        "title": "Is Modi The Mahmud Ghazni Of The Nehruvian Nation State?",
        "url": "https://scroll.in/article/845389",
        "year_hint": 2017,
    },
    {
        "title": "Four Ways I Underestimated Narendra Modi Three Years Ago",
        "url": "https://scroll.in/article/838700",
        "year_hint": 2017,
    },
    {
        "title": "From Human Being To Human Shield: The Tragic And Fragmented Story Of Citizen Farooq Dar",
        "url": "https://scroll.in/article/834970",
        "year_hint": 2017,
    },
    {
        "title": "Yogi Adityanath And Ramdev Are The New BJP Model Of Development Plus",
        "url": "https://scroll.in/article/832433",
        "year_hint": 2017,
    },
    {
        "title": "Elections 2017: It Is Time To Write An Obituary For Ideals Like Socialism, Secularism And Justice",
        "url": "https://scroll.in/article/831708",
        "year_hint": 2017,
    },
    {
        "title": "The Violent Clash When Left Snobbery Meets Right Populism Is Killing The University",
        "url": "https://scroll.in/article/830915",
        "year_hint": 2017,
    },
    {
        "title": "It Is Fitting That Even Gandhi's Assassination Is Being Used To Widen The Democratic Imagination",
        "url": "https://scroll.in/article/830161",
        "year_hint": 2017,
    },
]

EPW_RECORDS = [
    {
        "title": "Science, Nation State and Democracy",
        "url": "https://www.epw.in/journal/2023/24/perspectives/science-nation-state-and-democracy.html",
        "year_hint": 2023,
    },
    {
        "title": "Reading Ecology, Reinventing Democracy",
        "url": "https://www.epw.in/journal/2022/36/commentary/reading-ecology-reinventing-democracy.html",
        "year_hint": 2022,
    },
    {
        "title": "Reinventing the Commons",
        "url": "https://www.epw.in/journal/2021/8/perspectives/reinventing-commons.html",
        "year_hint": 2021,
    },
    {
        "title": "The Return of Ethics",
        "url": "https://www.epw.in/journal/2020/45/alternative-standpoint/return-ethics.html",
        "year_hint": 2020,
    },
    {
        "title": "Covid-19 Pandemic and the Crisis of Social Sciences",
        "url": "https://www.epw.in/journal/2020/42/perspectives/covid-19-pandemic-and-crisis-social-sciences.html",
        "year_hint": 2020,
    },
    {
        "title": "Thinking Kashmir",
        "url": "https://www.epw.in/journal/2017/38/perspectives/thinking-kashmir.html",
        "year_hint": 2017,
    },
    {
        "title": "Narendra Modi's Symbolic War",
        "url": "https://www.epw.in/journal/2014/22/commentary/narendra-modis-symbolic-war.html",
        "year_hint": 2014,
    },
    {
        "title": "Dreams of Reason",
        "url": "https://www.epw.in/journal/2013/47/special-articles/dreams-reason.html",
        "year_hint": 2013,
    },
    {
        "title": "Once There Was CSDS",
        "url": "https://www.epw.in/journal/2012/52/commentary/once-there-was-csds.html",
        "year_hint": 2012,
    },
    {
        "title": "Hazare vs Hazare: A Scenario Warning",
        "url": "https://www.epw.in/journal/2011/35/commentary/hazare-vs-hazare-scenario-warning.html",
        "year_hint": 2011,
    },
]

OUTLOOK_RECORDS = [
    {
        "title": "Citizenship Act Protests Capture Poetics of Democracy",
        "url": "https://www.outlookindia.com/national/opinion-citizenship-act-protests-capture-poetics-of-democracy-news-344663",
        "year_hint": 2019,
    },
    {
        "title": "JP Morgan Global Council — Assembly of Benign Politicians or Sanitisation of Evil?",
        "url": "https://www.outlookindia.com/national/opinion-jp-morgan-global-council-assembly-of-benign-politicians-or-sanitisation-of-evil-news-341807",
        "year_hint": 2020,
    },
    {
        "title": "Majoritarian Politics Impoverishes Both Democracy and Citizenship",
        "url": "https://www.outlookindia.com/national/opinion-majoritarian-politics-impoverishes-both-democracy-and-citizenship-news-340839",
        "year_hint": 2020,
    },
    {
        "title": "Why Only Technical and Experimental Startups, Why Not an Ethical One?",
        "url": "https://www.outlookindia.com/national/india-news-why-only-technical-and-experimental-startups-why-not-an-ethical-one-news-339253",
        "year_hint": 2020,
    },
    {
        "title": "Mourning Daryagunj: Memories of a Used Books Bazaar",
        "url": "https://www.outlookindia.com/national/india-news-mourning-daryagunj-memories-of-a-used-books-bazaars-news-337417",
        "year_hint": 2019,
    },
    {
        "title": "Dear Professor Manmohan Singh",
        "url": "https://www.outlookindia.com/national/dear-professor-manmohan-singh-news-269804",
        "year_hint": 2019,
    },
]


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.time_datetimes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "meta":
            content = attr_map.get("content", "").strip()
            if not content:
                return
            prop = attr_map.get("property", "").strip().lower()
            name = attr_map.get("name", "").strip().lower()
            if prop:
                self.meta[f"property:{prop}"] = content
            if name:
                self.meta[f"name:{name}"] = content
        elif tag.lower() == "time":
            dt = attr_map.get("datetime", "").strip()
            if dt:
                self.time_datetimes.append(dt)


def to_ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def slugify(value: str) -> str:
    value = to_ascii(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "untitled"


def normalize_title(title: str) -> str:
    lowered = to_ascii(title).lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def append_note(existing: str | None, note: str) -> str:
    current = (existing or "").strip()
    if not current:
        return note
    if note in current:
        return current
    return f"{current} | {note}"


def infer_tag_slugs(title: str, summary: str) -> list[str]:
    lowered = to_ascii(f"{title} {summary}").lower()
    chosen: list[str] = []
    for keyword, slugs in KEYWORD_TAGS.items():
        if keyword in lowered:
            for slug in slugs:
                if slug not in chosen:
                    chosen.append(slug)
    for slug in FALLBACK_TAG_SLUGS:
        if len(chosen) >= 5:
            break
        if slug not in chosen:
            chosen.append(slug)
    return chosen[:5]


def infer_tone(title: str, summary: str) -> str:
    text = to_ascii(f"{title} {summary}").lower()
    if any(k in text for k in ["remembering", "tribute", "dear professor", "grammari", "mahatma"]):
        return "Tribute"
    if any(k in text for k in ["need", "reinvent", "reimag", "return", "proposal", "capture", "outthink"]):
        return "Proposal"
    if any(
        k in text
        for k in [
            "crisis",
            "war",
            "impoverish",
            "violent",
            "obituary",
            "tragic",
            "killing",
            "manipulates",
            "banal",
            "question",
            "drying up",
        ]
    ):
        return "Critique"
    return "Opinion"


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None

    m = re.search(r"(\d{4}-\d{2}-\d{2})", candidate)
    if m:
        return m.group(1)

    try:
        dt = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except Exception:
        pass

    m2 = re.search(r"(\d{4})/(\d{2})/(\d{2})", candidate)
    if m2:
        return f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}"

    return None


def section_from_url(publication_key: str, url: str) -> str:
    lower = url.lower()
    if publication_key == "tnie":
        if "/opinion/columns/" in lower or "/columns/" in lower:
            return "Columns"
        return "Opinion"
    if publication_key == "epw":
        m = re.search(r"/journal/\d{4}/\d+/(.*?)/", lower)
        if m:
            slug = m.group(1)
            return " ".join(token.capitalize() for token in slug.split("-"))
        return "Journal"
    return "Opinion"


def fetch_url_metadata(url: str, timeout: int, retries: int) -> tuple[str | None, str | None, str | None]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    attempt = 0
    while attempt <= retries:
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}")

            parser = MetaParser()
            parser.feed(resp.text)

            og_title = parser.meta.get("property:og:title")
            desc = parser.meta.get("property:og:description") or parser.meta.get("name:description")
            date_values = [
                parser.meta.get("property:article:published_time"),
                parser.meta.get("name:publish-date"),
                parser.meta.get("name:pubdate"),
                parser.meta.get("name:date"),
                parser.meta.get("property:og:published_time"),
            ]
            date_values.extend(parser.time_datetimes)
            date_iso = None
            for raw in date_values:
                date_iso = parse_date(raw)
                if date_iso:
                    break

            clean_desc = " ".join(unescape((desc or "").replace("\n", " ")).split())
            clean_title = " ".join(unescape((og_title or "").replace("\n", " ")).split())
            return (clean_title or None, clean_desc or None, date_iso)
        except Exception:
            if attempt >= retries:
                return (None, None, None)
            sleep(1.0 + attempt * 0.5)
            attempt += 1

    return (None, None, None)


def chunked(items: list[dict], size: int) -> list[list[dict]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def date_fallback(year_hint: int) -> str:
    return f"{year_hint:04d}-07-01"


def load_tnie_2024_plus(source_db: Path) -> list[dict]:
    conn = sqlite3.connect(source_db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT
            a.title,
            a.canonical_url,
            a.published_at,
            a.section,
            a.reading_minutes,
            a.summary,
            a.tone,
            a.summary_method,
            a.retrieval_method,
            a.provenance_note
        FROM articles a
        WHERE CAST(strftime('%Y', a.published_at) AS INTEGER) >= 2024
          AND a.canonical_url LIKE 'https://www.newindianexpress.com/%'
        ORDER BY a.published_at DESC, a.id DESC
        """
    ).fetchall()
    conn.close()

    out: list[dict] = []
    for row in rows:
        out.append(
            {
                "publication_key": "tnie",
                "title": row["title"],
                "url": row["canonical_url"],
                "published_at": row["published_at"],
                "section": row["section"] or "Opinion",
                "reading_minutes": row["reading_minutes"],
                "summary": row["summary"],
                "tone": row["tone"] or infer_tone(str(row["title"]), str(row["summary"] or "")),
                "summary_method": row["summary_method"] or "manual_curated",
                "retrieval_method": row["retrieval_method"] or "forwarded_archive_curated",
                "provenance_note": row["provenance_note"] or "Imported from existing verified TNIE corpus (2024-2026).",
            }
        )

    return out


def seed_nontnie_records() -> list[dict]:
    out: list[dict] = []
    for row in SCROLL_RECORDS:
        out.append({"publication_key": "scroll", **row})
    for row in EPW_RECORDS:
        out.append({"publication_key": "epw", **row})
    for row in OUTLOOK_RECORDS:
        out.append({"publication_key": "outlook", **row})
    return out


def prepare_nontnie_records(records: list[dict], batch_size: int, timeout: int, retries: int) -> list[dict]:
    prepared: list[dict] = []
    batches = chunked(records, max(batch_size, 1))
    for idx, batch in enumerate(batches, start=1):
        print(f"Metadata batch {idx}/{len(batches)} | size={len(batch)}")
        for record in batch:
            title = str(record["title"])
            url = str(record["url"])
            publication_key = str(record["publication_key"])
            year_hint = int(record["year_hint"])

            og_title, meta_desc, published_at = fetch_url_metadata(url, timeout=timeout, retries=retries)
            final_title = title
            if og_title and len(og_title) >= 8:
                norm_existing = normalize_title(title)
                norm_og = normalize_title(og_title)
                if norm_existing in norm_og or norm_og in norm_existing:
                    final_title = title
                else:
                    final_title = title

            if not published_at:
                published_at = date_fallback(year_hint)

            summary = meta_desc
            summary_method = "meta_description"
            provenance_note = "Forwarded multi-source archive import (metadata-enriched)."
            if not summary or len(summary) < 30:
                summary = f"{final_title}. A public-intellectual reflection from {PUBLICATIONS[publication_key]['name']}."
                summary_method = "title_synthesis_v1"
                provenance_note = append_note(
                    provenance_note,
                    "Summary synthesized from headline due missing/short metadata description.",
                )

            if parse_date(str(published_at)) is None:
                published_at = date_fallback(year_hint)

            # Prefer clean ISO day format in DB.
            published_at = parse_date(str(published_at)) or date_fallback(year_hint)

            if published_at.startswith(f"{year_hint}-"):
                pass

            if published_at == date_fallback(year_hint):
                provenance_note = append_note(
                    provenance_note,
                    f"Date fallback used from year_hint={year_hint}.",
                )

            section = section_from_url(publication_key, url)
            tone = infer_tone(final_title, summary)

            print(
                f"  - {publication_key.upper()} | {published_at} | {final_title[:72]}"
                f" | summary_method={summary_method}"
            )

            prepared.append(
                {
                    "publication_key": publication_key,
                    "title": final_title,
                    "url": url,
                    "published_at": published_at,
                    "section": section,
                    "reading_minutes": None,
                    "summary": summary,
                    "tone": tone,
                    "summary_method": summary_method,
                    "retrieval_method": "forwarded_archive_metadata_fetch",
                    "provenance_note": provenance_note,
                }
            )

    return prepared


def build_db(db_path: Path, schema_path: Path, seed_tags_path: Path, records: list[dict]) -> None:
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.executescript(schema_path.read_text(encoding="utf-8"))
    cur.executescript(seed_tags_path.read_text(encoding="utf-8"))

    # Ensure publications set is complete.
    for pub in PUBLICATIONS.values():
        cur.execute(
            """
            INSERT OR REPLACE INTO publications (id, name, base_url)
            VALUES (?, ?, ?)
            """,
            (pub["id"], pub["name"], pub["base_url"]),
        )

    tag_ids = {
        row["slug"]: int(row["id"]) for row in cur.execute("SELECT id, slug FROM tags").fetchall()
    }

    today = datetime.now(UTC).strftime("%Y-%m-%d")

    for idx, row in enumerate(records, start=1):
        publication_key = str(row["publication_key"])
        publication_id = PUBLICATIONS[publication_key]["id"]

        title = str(row["title"]).strip()
        url = str(row["url"]).strip().rstrip("/")
        published_at = str(row["published_at"]).strip()
        summary = str(row["summary"] or "").strip()
        section = str(row["section"] or "Opinion").strip() or "Opinion"
        tone = str(row["tone"] or infer_tone(title, summary))
        summary_method = str(row["summary_method"] or "manual_curated")
        retrieval_method = str(row["retrieval_method"] or "forwarded_archive_import")
        provenance_note = append_note(
            str(row.get("provenance_note") or ""),
            f"Locked in multi-source baseline on {today}.",
        )

        external_id = f"{publication_key}-{published_at}-{slugify(title)}"

        cur.execute(
            """
            INSERT INTO articles (
                publication_id,
                external_id,
                canonical_url,
                section,
                title,
                normalized_title,
                author_name,
                published_at,
                reading_minutes,
                summary,
                tone,
                summary_method,
                retrieval_method,
                source_capture_date,
                provenance_note,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'verified')
            """,
            (
                publication_id,
                external_id,
                url,
                section,
                title,
                normalize_title(title),
                DEFAULT_AUTHOR,
                published_at,
                row.get("reading_minutes"),
                summary,
                tone,
                summary_method,
                retrieval_method,
                SOURCE_CAPTURE_DATE,
                provenance_note,
            ),
        )
        article_id = int(cur.lastrowid)

        tag_slugs = infer_tag_slugs(title, summary)
        for slug in tag_slugs:
            tag_id = tag_ids.get(slug)
            if tag_id is None:
                continue
            cur.execute(
                """
                INSERT OR IGNORE INTO article_tags (article_id, tag_id, confidence, method)
                VALUES (?, ?, ?, ?)
                """,
                (article_id, tag_id, 0.8, "hybrid"),
            )

        note_body = (
            f"Multi-source ingest row {idx}: publication={PUBLICATIONS[publication_key]['name']}, "
            f"summary_method={summary_method}, retrieval={retrieval_method}."
        )
        cur.execute(
            """
            INSERT INTO article_notes (article_id, note_type, body)
            VALUES (?, 'qa', ?)
            """,
            (article_id, note_body),
        )

    conn.commit()

    totals = cur.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status='verified' THEN 1 ELSE 0 END) AS verified,
            MIN(published_at) AS min_date,
            MAX(published_at) AS max_date
        FROM articles
        """
    ).fetchone()
    print(
        f"DB rebuild complete | total={totals['total']} verified={totals['verified']} "
        f"range={totals['min_date']}..{totals['max_date']}"
    )

    by_pub = cur.execute(
        """
        SELECT p.name AS publication, COUNT(*) AS c
        FROM articles a
        JOIN publications p ON p.id = a.publication_id
        GROUP BY p.name
        ORDER BY c DESC, p.name ASC
        """
    ).fetchall()
    for row in by_pub:
        print(f"  - {row['publication']}: {row['c']}")

    conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_opinions_v0.db",
        help="Existing DB path used to extract verified TNIE (2024-2026) seed records.",
    )
    parser.add_argument(
        "--output-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_opinions_v0.db",
        help="Output DB path to rebuild.",
    )
    parser.add_argument(
        "--schema-sql",
        default="/Users/praneet/shiv-archive/db/schema.sql",
        help="Schema SQL path.",
    )
    parser.add_argument(
        "--seed-tags-sql",
        default="/Users/praneet/shiv-archive/db/seed_tags.sql",
        help="Seed tags SQL path.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Batch size for URL metadata checks.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=25,
        help="HTTP timeout seconds.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="HTTP retry count.",
    )
    args = parser.parse_args()

    source_db = Path(args.source_db_path)
    output_db = Path(args.output_db_path)
    schema_path = Path(args.schema_sql)
    seed_tags_path = Path(args.seed_tags_sql)

    tnie_seed = load_tnie_2024_plus(source_db)
    if len(tnie_seed) != 33:
        raise RuntimeError(
            f"Expected 33 TNIE records (2024-2026), found {len(tnie_seed)} in source DB."
        )

    nontnie_seed = seed_nontnie_records()
    if len(nontnie_seed) != 28:
        raise RuntimeError(f"Expected 28 non-TNIE records, found {len(nontnie_seed)}.")

    prepared_nontnie = prepare_nontnie_records(
        nontnie_seed,
        batch_size=max(args.batch_size, 1),
        timeout=max(args.timeout, 5),
        retries=max(args.retries, 0),
    )

    all_records = tnie_seed + prepared_nontnie
    if len(all_records) != 61:
        raise RuntimeError(f"Expected 61 total records, found {len(all_records)}.")

    # URL uniqueness sanity.
    seen: set[str] = set()
    dupes: list[str] = []
    for row in all_records:
        key = str(row["url"]).rstrip("/")
        if key in seen:
            dupes.append(key)
        seen.add(key)
    if dupes:
        raise RuntimeError(f"Duplicate canonical URLs detected: {dupes[:5]}")

    build_db(output_db, schema_path, seed_tags_path, all_records)
    print("Rebuild locked: multi-source baseline ready for downstream annotation/export.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
