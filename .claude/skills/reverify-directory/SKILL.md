---
name: reverify-directory
description: Re-verify the Florida Rabbit Rescue Directory's listings end to end. Covers IRS 501(c)(3) status, the Florida Sunbiz corporate registry (bulk download, annual reports), websites, Facebook/Instagram activity, and Petfinder/Adopt-a-Pet listings. Reports findings and every blocked check to the maintainer, hands them exact URLs to check by hand, then applies the approved fixes, moves the site's "last verified" date and writes up the pass. Use this whenever the maintainer asks to re-verify, re-check, audit or refresh the directory, its rescues or its data, mentions the January re-verification, asks whether the listed rescues are still active, or wants to update the verified date, even if they don't say "skill".
---

# Re-verify the directory

A verification pass confirms that every organization in the main directory still exists, is still a
nonprofit, and is still operating. It also confirms that the links we publish for them still work.
The site's credibility rests on the "Last verified" date, so that date only moves when the checks
behind it have actually been done.

The work splits between you and the maintainer. You run everything that can be automated, then report
honestly, including **exactly where you were blocked**. The maintainer does the checks that need a
logged-in browser or a human eye, and approves every change to the live site. Expect several rounds of
back and forth; that is the normal shape of this job.

Default scope is the 14-or-so `organizations` (the main directory). `verify.py` also sweeps the other
sections, so report anything notable there briefly at the end.

## Ground rules, and why

- **HTTP 200 is not evidence that an organization exists.** Two defunct orgs once shipped as active
  because their websites kept answering. The state registry and annual-report filings are the strongest
  signals; a website or a Facebook date is supporting evidence only.
- **Never reclassify, remove or caveat a listing on an automated signal alone.** Report it, explain the
  evidence, and let the maintainer decide. A registry status of `I` is grounds to make contact, not to
  edit the site.
- **A push to `main` is a production deploy** (Netlify, live in ~15–30 s). Commit freely, but push only
  when the maintainer says so, and then confirm on the live URL.
- **Don't move `last_verified` until the maintainer has spot-checked the adoption listings** and approved
  the move. Petfinder can't be checked by script, so their check is what earns the new date.
- **501(c)(3) status is shown on each listing but is not a requirement** (see the site's About page). One
  listing has `not_found`. Don't treat a missing EIN as grounds for removal.
- **The repo is public.** Activity judgments about named rescues go in the gitignored
  `planning/verification-YYYY-MM.md`, not in tracked files. Commit messages carry the factual evidence
  for each data change (status codes, dates, who confirmed what).

## Phase 0: Orient

1. Read the newest `planning/verification-*.md` if one exists. Its "Next pass" list, open candidate
   rescues and "excluded as not rescues" list all carry forward. Also skim `RESUME-HERE.md`. Both are
   gitignored and may be missing on a fresh clone; that's fine.
2. Check `git status` is clean and note the current `meta.last_verified`.
3. Preserve the previous sweep's output before `verify.py` overwrites it:
   `cp -n planning/findings.json planning/findings-<previous YYYY-MM>.json`

## Phase 1: Automated sweep

Run `python3 scripts/verify.py` in the background (about 2 minutes, network only, read-only). It writes
`planning/findings.json` and prints these sections:

- **IRS anomalies.** Name-overlap flags for Bebette's, Marley's and Reba's are apostrophe artifacts, not
  discrepancies. Bugsy's has no EIN on record. Anything else (a revocation, a non-3 subsection) is real.
- **Unreachable sites.** A Facebook URL returning 400 is the script being blocked, not a broken page.
  `RemoteDisconnected` and some 403s are transient or bot-blocks: re-check with
  `curl -sL -A "<browser UA>" -w "%{http_code} %{url_effective}"` before treating them as findings. A
  500 on both urllib and curl is real.
- **Cross-domain redirects** (the merger detector). This is the highest-signal section. Every hit needs a
  browser look: is it the same organization on a new domain, or a merger?
- **Ceased-operation signals.** Read the context. Known, non-alarming hits are listed in the previous
  write-up.

Compare main-directory website results with the previous pass:

```bash
python3 -c "
import json
n={r['short_name']:r for r in json.load(open('planning/findings.json')) if r['section']=='organizations'}
o={r['short_name']:r for r in json.load(open('planning/findings-<prev>.json')) if r['section']=='organizations'}
for k,r in n.items():
  w=r['website']; ow=o.get(k,{}).get('website',{}); i=r['irs']
  print(f\"{k:22} IRS {i.get('subsection_code')}/{i.get('revoke_date')}  now {w.get('status')} {w.get('fetched_via')}  before {ow.get('status')}\")"
```

## Phase 2: Florida corporate registry (Sunbiz)

The `search.sunbiz.org` website sits behind a Cloudflare challenge, but the state publishes the whole
registry as a quarterly bulk download, and that covers everything the website would tell you.

1. **Check the server's files first** (no download):
   `expect .claude/skills/reverify-directory/scripts/sunbiz-get.exp "$PWD/planning/sunbiz" list`
   File dates should fall in the current quarter (the state regenerates them in January, April, July and
   October). If they don't, say the registry data is stale rather than letting the output look current.
2. **Download** (about 2 GB, about 6 minutes; run it in the background):
   `expect .claude/skills/reverify-directory/scripts/sunbiz-get.exp "$PWD/planning/sunbiz"`
   It needs an absolute path, and it answers the first-connection host-key prompt itself. Afterwards
   compare `ls -l planning/sunbiz/` byte counts with the `list` output; a truncated zip fails late and
   confusingly. Never unzip them (about 18.5 GB expanded).
3. **Run** `python3 scripts/verify_sunbiz.py` (about 80 s). Since October 2026 `cordata.zip` is Deflate64,
   which the script streams through `unzip -p` automatically.
4. **Confirm the parser is sane before trusting a clean run.** H.A.R.E. (`N04000011513`) must show filed
   `12/10/2004`, and Happy Bunny Rescue (`N23000014374`) must show status `I`. A one-byte offset shift
   produces plausible garbage, not an error.
5. **Read the output:**
   - Every listed org should be `A`. Closed orgs should stay `I`.
   - **The annual report column is the best activity signal there is.** Reports are due between
     January 1 and May 1. A listed org without a current-year report after May is worth raising. An org
     incorporated this year has none yet, and that's normal.
   - **Candidates not in the directory:** compare against the open-candidates and "excluded as not
     rescues" lists in the previous write-up. Only genuinely new names are news. A quick web search
     usually settles whether a new name is a rescue (a "krewe" turned out to be a Mardi Gras club).

If you change `verify_sunbiz.py`, run its tests: `python3 -m unittest discover -s tests`.

## Phase 3: Social and listing checks in a real browser

Scripts get uniform 400/403s from Facebook and Instagram, but a headless browser reads public pages:
page name, follower and post counts, and, on Facebook after scrolling, full post timestamps.

**Launch your own headless Brave** in the background (any Chromium browser with
`--remote-debugging-port` should behave the same, but only Brave has been tested):

```bash
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" --headless=new \
  --remote-debugging-port=9333 --no-first-run --no-default-browser-check \
  --disable-extensions --user-data-dir=<your scratch dir>/brave-cdp about:blank
until curl -s localhost:9333/json/version >/dev/null; do sleep 0.5; done
```

- Brave's own `--screenshot` flag hangs on this machine; driving it over the DevTools Protocol works.
- Another agent may be using headless Brave at the same time. Use your own `--user-data-dir` and port
  (set `CDP_PORT` for the scripts if you change it). When done, stop only your own instance:
  `pkill -f "user-data-dir=<your scratch dir>/brave-cdp"`. Never `pkill` Brave broadly.
- Run one page at a time; parallel captures in one browser produced garbled results.

**Then probe:**

```bash
S=.claude/skills/reverify-directory/scripts
python3 $S/social_urls.py > urls.tsv                 # every social, Linktree and listing URL
node $S/probe.mjs urls.tsv probe.json                # status, final URL, title, description, page text
python3 $S/social_urls.py facebook > fb.tsv
node $S/fb_dates.mjs fb.tsv                          # newest visible post dates per Facebook page
```

**Interpreting what comes back:**

- Instagram's description reads "N Followers, N Following, N Posts". Post dates are hidden logged out.
- **"This content isn't available right now"** (Facebook) or **"Profile isn't available"** (Instagram)
  can mean deleted, renamed, unpublished, or restricted to logged-in users. Before calling it broken,
  check whether the organization's own site still links to the same account:
  `curl -sL -A "<browser UA>" <their site> | grep -oE 'https?://(www\.)?(facebook|instagram)\.com/[^"'"'"' <>]+' | sort -u`
  Either way, it goes to the maintainer to check logged in.
- **Logged-out Facebook hides some recent posts.** H.A.R.E. showed nothing after 2024 logged out while
  being active logged in. A stale logged-out date is a reason for a logged-in look, never a dormancy
  finding on its own; weigh it against the annual report.
- Petfinder (Akamai 403 "temporarily unavailable" page) and Adopt-a-Pet (CloudFront 403) block headless
  browsers too. Those always go to the maintainer.

## Phase 4: Look into each anomaly

Before reporting, gather enough that the maintainer can decide without re-doing your work:

- **Website down:** check with curl and in the browser, load the hosting platform's root, and read the
  org's newest Facebook posts for an explanation (a move, a pause, a rebrand).
- **Cross-domain redirect:** load the final URL in the browser and confirm whose site it is.
- **Broken social or listing link:** find the current one on the org's own website or Linktree.
- **Suspicious IDs:** check the ID against the org's own link. A Petfinder member ID that lands on
  another organization's page is a wrong or reassigned ID.

## Phase 5: Report to the maintainer

Keep it scannable, lead with the verdict, and be explicit about what you could not check:

```markdown
**Verdict** (one or two sentences: closures/revocations/dissolutions? how many need attention?)

**Checks that passed for every organization:** IRS, Sunbiz (data quarter, Active count, annual
reports), websites, Facebook activity...

**Needs your attention:**
| Org | Finding (evidence, and what you think it means) |

**Where I was blocked:** each blocked source, how many orgs it affects, and what covers it instead
(if anything).

**Outside the main directory:** redirects, domain moves, new registry names (one line each).

**Decisions for you:** numbered, so they can answer "do 1 and 4, not 3".
```

## Phase 6: Hand the maintainer exact things to check

They can't act on "please check Petfinder". Give them a table of the exact URLs we publish (pull them
with `social_urls.py listing`) and say what to look for on each:

1. It opens that rescue's own profile, not an error, another organization or a generic search.
2. Name and city match. Petfinder sometimes shows the mailing city.
3. Pets are listed, ideally rabbits. Zero isn't a red flag by itself, but note it.

Put the orgs with the weakest other signals first. Add any logged-in social checks and any URL behind a
Cloudflare challenge that you couldn't see.

When something they report is broken, find the replacement from the org's own site or Linktree and
**have them confirm it before you commit**. Prefer Petfinder member URLs
(`https://www.petfinder.com/member/us/fl/<city>/<slug>-<id>/`) over search URLs, which have fallen back
to a generic location page. If you have to construct a URL, label it as a guess.

## Phase 7: Apply approved fixes

- Edit `directory-data.json` with exact, unique string replacements so the file's formatting survives.
  Validate (`python3 -c "import json; json.load(open('directory-data.json'))"`), run `npm run build`, and
  grep `_site/` to confirm the change rendered.
- **Visitor-facing notes go in `caveats`**, which renders as "Important notes" on the card.
  `directory_note` and `website_note` are internal and never displayed. If it's unclear which the
  maintainer means, ask.
- Copy rules: no em-dashes in site copy, neutral and factual, date-stamped. Example:
  "As of November 2026, the organization's website is down. According to their Facebook page, they are
  relocating."
- One commit per fix. The message records the evidence: what failed, with status codes and dates, where
  the replacement came from, and who confirmed it.
- Push only on approval, then confirm on the live site:
  `for i in $(seq 1 60); do curl -s https://floridarabbitrescues.org/directory/ | grep -q "<new text>" && break; sleep 3; done`

## Phase 8: Move the verified date (only when approved)

`meta.last_verified` drives the site-wide date. Each organization also has its own `last_verified`,
which renders on its card. Count before replacing, so nothing is half-updated:

```bash
grep -c '"last_verified": "<old YYYY-MM>"' directory-data.json   # expect 1 + number of organizations
```

Replace them all, confirm every organization now has the new value, build, and grep for the new
"Month YYYY" on `_site/index.html`, `_site/directory/index.html` and `_site/about/index.html`. Shelter
URL updates from redirect findings can go in the same commit. Push when approved and confirm live.

## Phase 9: Write it up and clean up

Create `planning/verification-YYYY-MM.md` (gitignored). Use the previous one as the model:

- **Header:** prior and new verified date, a one-line result, and the note that the file stays untracked.
- **What shipped:** commits table.
- **Per-organization results:** IRS, Sunbiz status, latest annual report, website, FB newest (logged
  out), IG posts.
- **Findings and how each was resolved,** including anything deliberately left as is, and why.
- **Methods:** anything that newly worked or newly broke, and **what is still blocked.**
- **Outside the main directory.**
- **Open work:** candidate rescues carried forward with fresh registry data, plus the "excluded as not
  rescues" list with any new names.
- **Next pass:** the specific things to look at first next time.

Then update `RESUME-HERE.md` if it exists, stop your Brave instance, and mention that the
`planning/sunbiz/*.zip` files (about 2 GB) are safe to delete; they re-download in minutes.

## Gotchas reference

| Symptom | Meaning |
|---|---|
| `NotImplementedError: That compression method is not supported` | Sunbiz zip uses a format Python can't read (Deflate64 since Oct 2026). The script handles it via `unzip -p`; if it recurs with a new method, the same fallback applies. |
| Brave `--screenshot` never returns | Known hang. Use CDP (Phase 3). |
| Lee County (`leefl.gov`) 403 in `verify.py` | Cloudflare bot check; it works in a browser. |
| Petfinder search URL shows a generic location page | The shelter filter was ignored (seen with a `shelter_id` search URL in 2026-11); use the member URL. |
| Petfinder member URL shows a different org | Wrong or reassigned ID; check the org's own site for theirs. |
| Sunbiz document number has 13 characters | Copied from a Sunbiz URL, which appends a sequence digit. Real numbers are `N` + 11 digits. |
| Org has no annual report this year | Fine if incorporated this year; worth raising after May 1 otherwise. |
| `verify.py` "unreachable" on a Facebook-only listing | The script is blocked; check it in the browser instead. |
