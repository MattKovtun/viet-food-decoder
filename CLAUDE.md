# CLAUDE.md — viet-food-decoder

Personal Vietnamese food decoder & selector, weighted to Da Nang / central Vietnam.
Owner lives in Da Nang; this is his own research tool, deployed static via GitHub Pages.
The repo is PUBLIC on GitHub — treat licensing, privacy and tone accordingly:
no personal data in committed files, no second-person prose in dish content.
Everything here is strictly vibe coded (AI-written, lightly human-reviewed) and the
README says so prominently — keep that note intact.

## What this project is

A one-pager (`index.html`) backed by a curated dataset (`data/dishes.json`) that:
1. **Decodes dish names** — Vietnamese dish names are compositional (`base + protein + method + place`);
   every dish stores its `parts` decomposition for color-coded rendering.
2. **Shows what a dish is** — image, plain description, literal meaning, rough pronunciation, region.
3. **Selects dishes by ingredients** — include/exclude over canonical ingredient tags, plus
   a spice filter (as-served heat, 0..3, with a "varies by stall" flag). The other flavor
   axes (sweet/sour/funk/rich) were dropped 2026-07-05 — too stall-dependent to be reference
   data; archived in data/flavor.archive.json. Do not resurrect them without owner say-so.

## Hard rules (do not violate)

- **Never scrape TasteAtlas** (or similar) — no bulk fetching of their API/pages/images, no copying
  their prose. Their dish *names/regions* may be used as a factual completeness checklist only.
  This was decided explicitly after discussion; do not re-litigate or quietly work around it.
- **Wikipedia/Wikimedia is the approved external source** (CC BY-SA 4.0). Any deployment must keep
  the attribution string (emitted into `data/wikipedia.raw.json` by the fetcher) in the site footer.
- **`data/dishes.json` is the single source of truth** in the final Dish schema. New dishes from the
  pipeline are NEVER auto-added — `merge` writes them to `data/candidates.review.json` (raw rows,
  different shape) for manual promotion. Keep it that way: curation stays deliberate.
- **Schema authority:** `src/models.py` (`Dish` dataclass + `Taxonomy` enums) is enforced truth;
  `data/schema.md` is its human-readable mirror. Change models.py first, run validate, then sync the doc.

## Layout

```
index.html                 # UI skeleton (small); loads static/style.css + static/app.js, no build step
static/style.css           # all page styles (CSS variables, light/dark)
static/app.js              # all page logic; fetches data/dishes.json; search mirrors TextNormalizer
main.py                    # CLI entry, minimal logic: fetch | merge | cache-images | gen-audio | validate
img/                       # cached dish images (960px Commons thumbs, committed; ~7.5 MB)
audio/                     # pronunciation MP3s, two voices per dish: <id>.mp3 female (HoaiMy),
                           # <id>-m.mp3 deep male (NamMinh); edge-tts, committed, ~1.9 MB
data/dishes.json           # 160 curated dishes (source of truth, final schema)
data/schema.md             # schema docs + design rationale
data/wikipedia.raw.json    # output of `fetch` (may not exist yet)
data/candidates.review.json# output of `merge` — raw stubs for manual review (NOT dish schema)
src/models.py              # Dish, RawWikiEntry, Taxonomy (enums: cats, forms, ~60 ingredient tags)
src/wikipedia_fetcher.py   # MediaWiki API fetch + wikitable parser; class WikipediaFetcher
src/merger.py              # DatasetMerger: fills Commons img URLs, emits candidates + report
src/image_finder.py        # ImageFinder: Commons search API for imageless dishes (NOT Google — licensing)
src/image_cacher.py        # ImageCacher: downloads img -> img/<id>.<ext>, fills img_local
src/audio_generator.py     # AudioGenerator: edge-tts (vi-VN-HoaiMyNeural) -> audio/<id>.mp3, fills audio
src/utils.py               # TextNormalizer: diacritic-insensitive normalize/slug (đ/Đ handled)
tests/test_parser.py       # fixture test: run `.venv/bin/python -m tests.test_parser`
```

## Commands

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py validate    # schema-check dishes.json — run after ANY data edit
.venv/bin/python main.py fetch       # needs internet: pulls the two Wikipedia list pages
.venv/bin/python main.py merge       # fills images; prints matched/images_filled/new_candidates
.venv/bin/python main.py find-images   # Commons search fills img for imageless dishes; REVIEW every pick visually —
                                       # search hits can be absurdly wrong (an Audi "e-tron" matched "mít trộn")
.venv/bin/python main.py cache-images  # downloads imgs -> img/, fills img_local; idempotent, run after merge/promotion.
                                       # Also ADOPTS owner photos: drop img/<dish-id>.jpg for an imageless dish and it
                                       # gets img_local + img_verified + own-photo src automatically
.venv/bin/python main.py gen-audio     # TTS pronunciation -> audio/, fills audio; idempotent, needs internet (one-time per dish)
.venv/bin/python -m tests.test_parser
```

## Schema quick reference (full docs: data/schema.md)

Dish fields: `id, name, parts[[text,kind]], pron, lit, desc, region, central(bool), cat, form,
ingredients[tags], spice(0..3), spice_varies(bool), aka[], variants[{name,note}],
history, img, img_verified(bool), img_query, img_local, audio, audio_m, srcs[]`.
- `history` = origin + cultural impact prose (handbook content); collapsed in the UI, excluded
  from search on purpose (long prose would make every query match everything).
- `aka` = pure synonyms (nem rán → chả giò); `variants` = order-variants that change what arrives
  (bún giò → pork knuckle instead of beef). Both searchable. Menu strings like "bún giò bò" map to
  their dish family (bún bò Huế) with the difference explained in the variant note — variants that
  only swap toppings do NOT get their own dish entry.
- `parts` kinds: base | protein | method | place | form | plain (drives colored name rendering)
- `central: true` = Da Nang/Quảng Nam/Huế/Hội An specialty — shown as an explicit
  "central VN specialty" badge in the UI (owner rejected a bare ★ symbol as unclear)
- `spice` = heat AS SERVED; `spice_varies` = stall-dependent (UI shows "🌶 varies" + warning note).
  Owner field reports override desk ratings — e.g. bún bò Huế demoted 3→1+varies after he ate
  an actually-mild bowl in Da Nang (Huế-style shops run hotter; chili sate lives on the table).
- `img_verified` = image from curated Wikipedia-list match, not Commons keyword search (★ in UI)
- `img`: Wikimedia Commons URL only (hotlink-safe, licensed) — stays the provenance/attribution
  link even when cached. `img_query`: search fallback. `img_local`: repo-relative cached copy
  (`img/<id>.<ext>`), filled by `cache-images`; UI prefers local → thumb → original.
  Store the ORIGINAL file URL in `img`; thumbs are derived. Wikimedia serves anonymous thumbs
  only at fixed widths 120/250/330/500/960/1280 (https://w.wiki/GHai) — other widths return 400.
- `srcs`: provenance — "handbook" (original content), "wikipedia" (CC BY-SA), later "own-photo"

## Conventions (from owner's python-expert skill — apply to all Python work)

- Always run inside `.venv`; keep `requirements.txt` and `README.md` synced after changes.
- Class-based components, type hints everywhere, no `global`, no imports inside functions,
  no `../` imports; absolute imports from `src.`.
- `.gitignore` must contain `.venv/`, `__pycache__/`, `.env`, `*.pyc`.
- Config via env vars with sane defaults (see `.env.example`: WIKI_API_URL, WIKI_USER_AGENT).

## Owner preferences (matter more than usual)

- **Comprehensive over curated** — full coverage, complete reference material; never trim to a "top N".
- Direct, honest pushback expected; validate ideas on logic, not politeness.
- Practical framing: he's on the ground in Da Nang (heat, scooter, child, budget are real constraints).
- Durable deliverables: standalone reusable files over inline answers.

## Street-sighting workflow (systematic dish intake)

Owner sees dishes on the street faster than we cover them. The loop:

1. **Capture** — owner reports a menu string (chat or `data/sightings.json`). Log it there
   verbatim with where/when. Zero friction beats perfect data.
2. **Triage** each sighting, in this order:
   - already a dish? (search name + aka, diacritic-insensitive) → status `covered`
   - same bowl, other name? → add to that dish's `aka` → `alias-added`
   - same dish, different topping/order? → add to `variants` (with spice if it differs) → `variant-added`
   - genuinely new dish → write a FULL entry (all fields incl. history read), insert near
     its category siblings → `promoted`
   - not a dish (condiment, ingredient, generic category, stove...) → `rejected` + why
   - can't identify confidently → stays `open` with questions for the owner; NEVER invent
     an entry from a guess — owner eats it, reports contents, then we write it.
3. **Assets** for promoted dishes: `gen-audio` (idempotent), image via `find-images` only if
   Commons plausibly has it (else img_query fallback + owner photo), `cache-images`, `validate`.
4. **Backlog** — `data/coverage.todo.md` holds the triaged Wikipedia-candidate backlog
   (107 stubs from candidates.review.json, tiered by street-relevance). Promote in small
   batches, owner picks; keep counts in README/CLAUDE.md in sync.
5. Owner field reports ALWAYS override desk data (spice, contents, names).

## State & roadmap

Done:
- [x] Schema + Taxonomy, validated dataset of 160 dishes (all hand-tagged ingredients + spice)
- [x] Wikipedia fetch/merge pipeline, parser fixture-tested (thumb→original URL upgrade works)
- [x] Earlier standalone artifact: vietnam-food-handbook.html (predecessor; dataset supersedes it)
- [x] `fetch` + `merge` ran: wikipedia.raw.json + candidates.review.json exist; 50/79 imgs filled
- [x] `index.html` one-pager (pure HTML/CSS/JS, mobile-first, dark-mode aware): color-coded
   decoding, diacritic-insensitive search (JS mirrors `TextNormalizer` — keep in sync),
   category filter (owner removed the central-VN filter chip 2026-07-05; `central` stays
   as a badge in the dish view only), quick mild-spice chip, tri-state ingredient
   include/exclude, spice filter, ingredient tags on cards, detail overlay with 960px Commons thumb
   (onerror → original file → `img_query` search link), deep links via `#dish-id`,
   CC BY-SA footer. Logic smoke-tested in Node against the full dataset.
- [x] Image cache: `cache-images` command + `img_local` field; all 50 images downloaded to
   img/ (960px thumbs), UI serves them locally with Commons fallback + per-dish credit link.

Next (in order):
1. Work the intake system: `data/sightings.json` (street inbox) + `data/coverage.todo.md`
   (triaged 107-stub backlog, Tier A first). Promote in small batches; re-run `validate`.
2. GitHub Pages deploy (repo root). Footer attribution already in place.
3. Later: own-photo workflow (photos committed to repo, `srcs` gains "own-photo");
   gap-check dish list by eye against TasteAtlas names (facts only).
