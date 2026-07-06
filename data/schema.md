# Dataset schema — data/dishes.json

Every entry in `dishes[]`:

| field | type | meaning |
|---|---|---|
| `id` | string | slug, unique (`mi-quang`) |
| `name` | string | canonical Vietnamese name with diacritics |
| `aka` | string[] | pure synonyms — same bowl under another name (e.g. `nem rán` → chả giò, `bún bò giò heo` → bún bò Huế); searchable, shown as "also: …"; optional |
| `variants` | {name, note, spice?}[] | order-variants that change what arrives (e.g. `bún giò` = pork knuckle instead of beef); searchable, rendered as a "Variants — how to order" table in the dish view with a chili indicator per row (`spice` overrides the dish's heat when a variant differs; omitted = inherit); optional |
| `history` | string | origin story + cultural impact — a multi-paragraph "waiting for your food" read (markdown-lite: blank-line paragraphs, `[text](https://url)` links, mostly to Wikipedia); collapsed `<details>` with a min-read hint at the bottom of the dish view, NOT searchable (long prose would pollute search results); no second-person prose (public repo); optional |
| `parts` | [text, kind][] | name decomposition; kind ∈ `base, protein, method, place, form, plain` — drives the color-coded rendering |
| `pron` | string | rough romanised pronunciation, tones dropped (memory aid only) |
| `lit` | string | literal word-by-word meaning; "(debated)" marks unsettled etymology |
| `desc` | string | one-to-two-line plain description of what arrives on the table |
| `region` | string | free-text origin/associated region |
| `central` | bool | true = Da Nang / Quảng Nam / Huế / Hội An specialty — "central VN specialty" badge + "Central VN only" filter in the UI |
| `cat` | enum | `noodle-soup, noodle-dry, rice, roll, cake, main, snack, sweet, drink` |
| `form` | enum | how it eats: `broth, semi-dry, dry, roll, rice, cake, snack, sweet, drink, hotpot` |
| `ingredients` | string[] | canonical tags (see `src/models.py: Taxonomy.INGREDIENTS`) — powers include/exclude selection |
| `spice` | int | 0–3, heat level **as served** (the four other flavor axes were removed 2026-07-05 as too stall-dependent; archived in `data/flavor.archive.json`) |
| `spice_varies` | bool | true = heat depends heavily on the stall (bánh mì chili spread, ốc, lẩu…); the UI shows "🌶 varies" and a check-before-ordering note |
| `img` | string\|null | Wikimedia Commons URL (licensed, hotlinkable); filled by `merge` — kept as the provenance/attribution link |
| `img_verified` | bool | true = image came from the curated Wikipedia-list match (`merge`); false = found via Commons keyword search (`find-images`) or no image. Shown as ★ in the UI |
| `img_query` | string | fallback image-search query when `img` is null |
| `img_local` | string\|null | repo-relative cached copy (`img/<id>.<ext>`), filled by `cache-images`; the UI prefers it and falls back to `img` |
| `audio` | string\|null | pronunciation clip, female voice (`audio/<id>.mp3`, vi-VN neural TTS), filled by `gen-audio`; UI 🔊 buttons play it, falling back to browser speech synthesis |
| `audio_m` | string\|null | pronunciation clip, deep male voice (`audio/<id>-m.mp3`, vi-VN-NamMinhNeural), filled by `gen-audio`; "deep voice" button in the dish view |
| `srcs` | string[] | provenance: `handbook` (our original content), `wikipedia` (CC BY-SA facts/images), later `own-photo` |

Design decisions:
- **Ingredients are dish-defining tags, not full recipes** — enough for "show me pork + no fermented sauce", not for cooking.
- **Only spice survived the flavor axes** (owner decision, 2026-07-05): sweet/sour/funk/rich vary too much stall-to-stall to be reference data. Spice is kept because "will this burn me as served" is a real decision input, refined by `spice_varies` for vendor-dependent dishes. The old five-axis data lives in `data/flavor.archive.json`.
- **New dishes from Wikipedia are never auto-merged** — they land in `candidates.review.json` for manual curation, so quality stays deliberate.

Attribution requirement: any deployment must credit Wikipedia (CC BY-SA 4.0) in the footer — the string is emitted into `wikipedia.raw.json` by the fetcher.
