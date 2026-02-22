# Shiv Vishwanathan Opinions Atlas

## Vision
Build a public, free website that archives and analyzes Shiv Vishwanathan opinion pieces from The New Indian Express, starting with a reliable corpus and growing into an interactive sociological, policy, and anthropological exploration.

## v0.1 Outcome (First Public Launch)
v0.1 is a browsable corpus release. Each article record must include:
- title
- publish date
- source URL
- short summary
- analytical tags

Users can:
- browse all records
- search by title text
- filter by year and tags
- open the original article URL

## Long-Term Product Roadmap
- v0.1: Corpus browser (metadata + summary + tags)
- v0.2: Timeline + tag trend analysis (yearly and thematic shifts)
- v0.3: Concept map/network visualization (co-occurring themes)
- v1.0: Public data release, methods page, reproducible pipeline

## Delivery Strategy

### Workstream A: Corpus and Data Quality
1. Build article registry from screenshots and URLs.
2. Store every source asset (screenshots, OCR text, provenance).
3. Add verification status per article (`draft`, `verified`, `published`).
4. Prevent duplicates by canonical URL and normalized title/date checks.

### Workstream B: NLP for Summaries and Tags
1. Start with hybrid tagging:
   - keyword extraction
   - taxonomy mapping
   - manual review pass
2. Keep confidence scores and method provenance for every tag.
3. Maintain a controlled vocabulary with domains:
   - sociology
   - policy
   - anthropology
   - cross_cutting

### Workstream C: Public Website
1. Launch as a free static-first site.
2. Render cards for all articles with filters and sorting.
3. Publish a short methodology page describing:
   - data source and scope
   - summary generation method
   - tag methodology and caveats

### Workstream D: Governance and Ethics
1. Keep only metadata, summaries, tags, and links in public output.
2. Do not republish full article text unless explicit rights are confirmed.
3. Track source and transformation provenance for each record.

## v0.1 Acceptance Criteria
- Article table populated and queryable.
- Each published record has at least:
  - 1 summary
  - 3 tags
  - 1 source URL
- Search/filter response under 1 second for expected corpus size.
- Mobile and desktop views work.
- Public URL is live and free to access.

## Suggested 6-Week Timeline
1. Week 1: Schema setup, ingestion template, first 50 records.
2. Week 2: OCR-assisted ingestion, dedupe rules, verification workflow.
3. Week 3: Summary and tag pipeline baseline + manual QA pass.
4. Week 4: v0.1 frontend (browse, search, filters, detail view).
5. Week 5: Data cleanup, performance, methodology page, soft launch.
6. Week 6: Public launch, feedback loop, v0.2 planning.

## Immediate Next Actions
1. Begin populating `articles` from screenshots and known URLs.
2. Verify 20 records end-to-end (ingest -> summary -> tags -> publish).
3. Stand up minimal frontend on free hosting.
4. Publish v0.1 once verified coverage is acceptable.
