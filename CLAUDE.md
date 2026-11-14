# CLAUDE.md

A static directory of verified Florida rabbit rescues, live at https://floridarabbitrescues.org.
It uses Eleventy 3 + Nunjucks + vanilla CSS, with Pagefind for search. There is no framework and no client-side app.

## Commands

```
npm run build                      # eleventy + pagefind -> _site/
npm run serve                      # build, then live-reload preview
python3 scripts/verify.py          # re-verification sweep, network only, ~2 min, read-only
python3 scripts/verify_sunbiz.py   # FL corporate registry check; skips cleanly without bulk data
python3 -m unittest discover -s tests   # unit tests for the verify scripts (stdlib only)
```

Node 20 (`netlify.toml`). The site itself has no test suite. "Verified" means the build succeeds and the
pages render correctly. For data changes, it also means the verify scripts are clean. Both scripts
document their method, limits and setup in their module docstrings. Read those before running or
changing them. `tests/fixtures/cordata-deflate64.zip` holds synthetic records only. It was made with
`7zz a -tzip -mm=Deflate64` (brew `sevenzip`), because Python cannot write Deflate64.

Deploy: pushing to `main` triggers a Netlify rebuild, and the site is live in about 30s. **A push to main is a
production deploy.** Confirm changes on the live URL.

## Architecture

`directory-data.json` is the single source of truth. `src/_data/directory.js` loads it as the
`directory` global, `src/_data/site.js` holds site-wide SEO constants, and `src/_includes/base.njk`
is the single layout (nav, search, meta/OG/JSON-LD, footer). Filters live in `eleventy.config.js`.

| Key in `directory-data.json` | Renders at |
|---|---|
| `organizations` | `/directory/` (main listings) |
| `excluded_organizations` | `/other-rescues/` (multi-species orgs) |
| `shelters_and_services` | `/shelters/`, grouped by region |
| `closed_organizations` | `/directory/`, only entries with `show_in_ui: true` |
| `organizations_watching` | nowhere (intentionally) |
| `meta.last_verified` | site-wide "Last verified" date |

**Never hand-write a count in page copy.** Use `{{ directory.<array> | length }}`, so adding or
removing an entry needs no copy edits.

## Silent-failure traps

- `groupByRegion` only renders the five regions in its `regionOrder`. A shelter with any other
  `region` string disappears from `/shelters/` without an error.
- A new `model` or `species_focus` value needs an entry in `modelLabel` / `speciesLabel`.
  Without one, it renders as the raw snake_case key.
- `last_verified` (both `meta` and per-org) must be `YYYY-MM`, because `friendlyMonth` parses it.
- Sunbiz document numbers are 12 characters (`N` + 11 digits). Sunbiz result URLs append a 13th
  sequence digit, so don't copy the number from the URL (see `scripts/verify_sunbiz.py`).
- An HTTP 200 does not show that an organization still exists. Defunct orgs have kept live sites. The
  state registry and cross-domain redirects are what catch them.

## Data conventions

- Main directory criteria are on `/about/`: Florida-based, rabbit-focused, currently active.
  501(c)(3) status is shown per listing via `nonprofit.status`.
- `shelters_and_services` is a deliberately lower bar ("may have rabbits available"), and its schema is
  only `{name, url, region}`. Confirm rabbits somehow, and record the evidence in the commit
  message, since the data file has nowhere to hold it. Keep the array sorted case-insensitively.
- Presentation is neutral and factual: never rank, score or promote an organization. Mission
  statements are verbatim where possible.
- Site prose uses no em-dashes. Use commas, colons or periods instead. An em-dash used as a list
  separator (e.g. "Name — reason" in Closed Organizations) is fine.

## Re-verification

The full listing re-verification (scripts, Sunbiz download, browser checks of social and adoption
listings, maintainer hand-offs, verified-date move) is the `reverify-directory` skill in
`.claude/skills/reverify-directory/`. Follow it rather than improvising.

## Local-only files

`planning/`, `RESUME-HERE.md` and `SESSION-NOTES.md` are gitignored and may not exist in a
given checkout. When present, `RESUME-HERE.md` holds the current status and next steps, and
`planning/findings.json` is where `verify.py` writes its output.
