# viet-food-decoder

Personal Vietnamese food decoder & selector, weighted toward Da Nang / central Vietnam.
A static one-pager (search, dish-name decoding, ingredient & spice filters, pronunciation
audio, history reads) backed by a hand-curated dataset of 160 dishes and a small Python
pipeline that pulls facts and images from Wikipedia/Wikimedia Commons.

> **NOTE: everything in this repo is strictly vibe coded.** All code, data tagging, prose
> and pipeline were produced in conversation with an AI assistant (Claude), reviewed only
> lightly by a human who mostly wanted lunch. Treat code quality, factual claims and
> spice ratings accordingly — corrections welcome.

Built for one person's phone, in front of one menu at a time. Not a restaurant guide,
not a product — but if it helps you order the right bowl, great.

## Layout

```
├── index.html                 # UI skeleton; loads static/ assets (no build step)
├── static/                    # style.css + app.js (app.js reads data/dishes.json)
├── main.py                    # CLI: fetch | merge | cache-images | validate
├── img/                       # cached dish images (960px Commons thumbs, committed)
├── audio/                     # pronunciation MP3s (Vietnamese neural TTS, committed)
├── data/
│   ├── dishes.json            # curated dataset (160 dishes) — the source of truth
│   ├── schema.md              # field & taxonomy documentation
│   ├── wikipedia.raw.json     # produced by `fetch` (not committed until you run it)
│   └── candidates.review.json # produced by `merge` — new-dish stubs to review by hand
├── src/
│   ├── models.py              # Dish / RawWikiEntry dataclasses + Taxonomy enums
│   ├── wikipedia_fetcher.py   # MediaWiki API fetch + wikitable parser (CC BY-SA source)
│   ├── merger.py              # fills images, reports unmatched candidates
│   └── utils.py               # diacritic-insensitive normalization
└── tests/test_parser.py       # parser fixture test
```

## Setup

```bash
uv venv
uv pip install -r requirements.txt
```

## Pipeline

```bash
.venv/bin/python main.py validate   # schema-check dishes.json (160 OK)
.venv/bin/python main.py fetch      # pull the two Wikipedia list pages -> data/wikipedia.raw.json
.venv/bin/python main.py merge      # fill Commons image URLs; write candidates.review.json
.venv/bin/python main.py find-images  # Commons search for still-imageless dishes; review picks, then cache-images
.venv/bin/python main.py cache-images  # download images -> img/, fill img_local (idempotent)
.venv/bin/python main.py gen-audio     # TTS pronunciation clips -> audio/, fill audio (idempotent)
.venv/bin/python -m tests.test_parser
```

Note: `fetch` needs normal internet access (en.wikipedia.org). Run it locally —
it was authored and fixture-tested in a sandbox whose egress allowlist blocks wikipedia.

## Running the site

`index.html` is fully static and fetches `data/dishes.json` at runtime, so it needs to be
served over HTTP (opening it as `file://` blocks the fetch):

```bash
.venv/bin/python -m http.server        # then open http://localhost:8000
```

Alternatively, in VS Code the [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer)
extension works too — "Go Live" on the repo root and it serves `index.html` with auto-reload.

Deployment is handled by GitHub Actions (`.github/workflows/pages.yml`): every push to
`main` publishes the repo root to GitHub Pages — no build step. One-time setup: in the
repo settings, set **Pages → Source → GitHub Actions**. Deep links work: `index.html#mi-quang`
opens that dish directly.

Images are served from the repo (`img/`, cached by `cache-images`), so the site works
without hitting Wikimedia. Fallback chain per dish: local copy → Commons 960px thumb →
Commons original. Note: Wikimedia only serves thumbnails at fixed widths to anonymous
clients (120/250/330/500/960/1280 px — see https://w.wiki/GHai). After promoting new
dishes or when `merge` fills new image URLs, re-run `cache-images` (existing files are
kept; delete a file to force re-download).

Pronunciation: each dish has two committed MP3s (`audio/`, generated once via `gen-audio`
with Microsoft Edge's vi-VN neural voices) — `<id>.mp3` female (HoaiMy) and `<id>-m.mp3`
deep male (NamMinh). The 🔊 buttons play the local files; if a dish has no clip yet, the
browser's own Vietnamese speech synthesis is used as fallback. After promoting new
dishes, re-run `gen-audio`.

## Data licensing

- `handbook`-sourced fields (decomposition, pronunciations, spice ratings, descriptions, history): original content.
- Wikipedia-derived facts/descriptions/images: CC BY-SA 4.0 — keep the attribution string
  from `wikipedia.raw.json` in the site footer. Commons images carry individual free licenses;
  the cached copies in `img/` keep their attribution via the per-dish Commons link in the UI
  (`img` stays the source URL).

## Next

1. Work through `data/coverage.todo.md` (triaged backlog of 107 Wikipedia candidates) and
   `data/sightings.json` (street-sighting inbox) — promote in small batches, re-run `validate`.
2. Enable GitHub Pages (Settings → Pages → Source: GitHub Actions) — the deploy workflow
   is in place. The CC BY-SA attribution is already in the page footer.
3. Later: own-photo workflow (`srcs` gains `own-photo`); gap-check dish list against
   TasteAtlas names (facts only, no scraping).
