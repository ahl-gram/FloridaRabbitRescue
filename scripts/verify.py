"""Re-verification sweep for the Florida Rabbit Rescue Directory.

Periodic re-verification of every organization listed in directory-data.json. Read-only:
it reports, and never edits the data.

Run:  python3 scripts/verify.py

Output goes to planning/findings.json, which is not tracked in this repository.

Sections covered: `organizations` (14), `excluded_organizations` (12, rendered at
/other-rescues/), `shelters_and_services` (19), `closed_organizations` (3).
`organizations_watching` is empty and renders nowhere, so it is skipped by design.

Automatable signals:
  - IRS exempt status via ProPublica Nonprofit Explorer API (by EIN)
  - stored-name vs IRS legal-name divergence
  - cross-domain redirects, which is the merger/rebrand fingerprint
  - website reachability AND ceased-operation content signals

NOT automatable, must be done in a browser or left flagged:
  - Sunbiz corporate status  -> Cloudflare JS challenge, no scripted access at any UA
  - Petfinder membership     -> 403 to scripts; a quit org 403s identically to an active one.
                                There is no API alternative: Petfinder decommissioned its public
                                API on 2025-12-02 and api.petfinder.com no longer resolves. Its
                                replacement is a display-only widget. Adopt-a-Pet and Shelterluv
                                both have live APIs but scope keys to the organization's own data,
                                so neither is usable by a third-party directory.
  - Facebook / Instagram     -> uniform 400/403 bot-blocking, zero signal, not worth the requests
  - founded year, board      -> no machine-checkable source

The hard-won lesson: HTTP 200 is not evidence an organization still exists. The Humane Society
of Pinellas returned 200 for four months after it merged out of existence. What WOULD have
caught it is the cross-domain redirect check, so treat that section of the output as the
highest-signal part of a run.

Known urllib false positives, all confirmed serving fine via curl (do not chase these):
  - hare.as.miami.edu          -> ERR:URLError, TLS handshake (UNEXPECTED_EOF)
  - humanesocietytampabay.org  -> 500
  - fkspca.org                 -> 403
  - any facebook.com URL       -> 400
Confirm any non-200 with `curl -sIL <url>` before treating it as a real finding.
"""

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
DATA_PATH = os.path.join(ROOT, "directory-data.json")
# Output lands in planning/, which is gitignored, so sweep results stay untracked.
OUT_DIR = os.path.join(ROOT, "planning")
OUT_PATH = os.path.join(OUT_DIR, "findings.json")

# Names below 1.0 overlap are worth a human look. Do not raise this floor:
# Fort Wilbur surfaced at 0.6, and apostrophes alone push a clean match to 0.4.
NAME_REVIEW_THRESHOLD = 1.0

CEASED_PATTERNS = [
    r"no longer (?:accepting|operating|taking|in operation)",
    r"permanently closed",
    r"we (?:have )?closed",
    r"ceased operations",
    r"not accepting (?:new )?(?:rabbits|surrenders|intakes|applications)",
    r"intake (?:is )?(?:closed|paused|suspended|on hold)",
    r"adoptions (?:are )?(?:closed|paused|suspended|on hold)",
    r"temporarily closed",
    r"dissolv(?:ed|ing)",
    r"shutting down",
    r"domain (?:is )?for sale",
]

STOPWORDS = {"inc", "incorporated", "of", "the", "a", "and", "&", "llc",
             "corp", "corporation", "co", "foundation", "fl", "florida"}


def fetch(url, timeout=25):
    """Return (status, body_text, final_url). status is an int, or 'ERR:Type'.

    Note: some hosts (hare.as.miami.edu) fail urllib's TLS handshake with
    UNEXPECTED_EOF while serving curl fine. An ERR: result means "no signal",
    not "site is down" -- confirm with curl before concluding anything.
    """
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/json,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode(
                r.headers.get_content_charset() or "utf-8", errors="replace")
            return r.status, body, r.url
    except urllib.error.HTTPError as e:
        # e.url is the URL that actually errored, i.e. the END of the redirect
        # chain. Returning the original `url` here would throw away the
        # cross-domain hop, which is the one signal worth having.
        return e.code, "", (getattr(e, "url", None) or url)
    except Exception as e:
        return f"ERR:{type(e).__name__}", "", url


def host_of(url):
    return urllib.parse.urlparse(url or "").netloc.lower().removeprefix("www.")


def redirect_note(url, final_url):
    """A cross-domain redirect is the fingerprint of a merger or acquisition.

    This is what would have caught the Humane Society of Pinellas: its URL kept
    returning 200, but it had started 301ing to humanesocietytampabay.org. Same
    host with a different path is just normalization and is not interesting.
    """
    a, b = host_of(url), host_of(final_url)
    if a and b and a != b:
        return f"CROSS-DOMAIN REDIRECT {a} -> {b} (merger? rebrand? check it)"
    return None


def tokens(name):
    words = re.findall(r"[a-z0-9]+", (name or "").lower())
    return {w for w in words if w not in STOPWORDS}


def name_overlap(stored, official):
    """Token overlap, 1.0 = same significant words, 0.0 = unrelated."""
    a, b = tokens(stored), tokens(official)
    if not a or not b:
        return None
    return round(len(a & b) / len(a | b), 2)


def strip_html(html):
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def ceased_signals(body):
    """Regex hits for 'we stopped operating' language, with context.

    Expect false positives: 'an animal you can no longer care for' matches.
    Always read the context before acting on a hit.
    """
    text = strip_html(body)
    hits = []
    for pat in CEASED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            lo, hi = max(0, m.start() - 130), m.end() + 150
            hits.append({"pattern": pat, "context": text[lo:hi]})
    return hits


def check_irs(ein):
    if not ein:
        return {"checked": False, "reason": "no EIN on record"}
    status, body, _ = fetch("https://projects.propublica.org/nonprofits/api/v2"
                            f"/organizations/{re.sub(r'[^0-9]', '', ein)}.json")
    if status != 200:
        return {"checked": False, "reason": f"API returned {status}"}
    try:
        org = json.loads(body).get("organization", {}) or {}
    except json.JSONDecodeError:
        return {"checked": False, "reason": "unparseable API response"}
    return {
        "checked": True,
        "irs_name": org.get("name"),
        "revoke_date": org.get("revoke_date"),
        "subsection_code": org.get("subsection_code"),
        "city": org.get("city"),
        "state": org.get("state"),
    }


def check_site(url):
    if not url:
        return {"checked": False, "reason": "no website on record"}
    status, body, final_url = fetch(url)
    out = {"checked": True, "status": status, "final_url": final_url}
    note = redirect_note(url, final_url)
    if note:
        out["redirect_note"] = note
    if status == 200 and body:
        out["ceased_signals"] = ceased_signals(body)
    return out


def sweep_main_orgs(data):
    findings = []
    for org in data["organizations"]:
        np_ = org.get("nonprofit") or {}
        rec = {
            "section": "organizations",
            "short_name": org["short_name"],
            "stored_name": org["name"],
            "stored_last_verified": org.get("last_verified"),
            "irs": check_irs(np_.get("ein")),
            "website": {"url": org.get("website"), **check_site(org.get("website"))},
            "unverifiable": {
                "sunbiz_status": "Cloudflare JS challenge; browser-only",
                "petfinder_membership": "403 to scripts; no signal either way",
                "founded_year": f"stored {org.get('founded')}; source not machine-checkable",
                "board": f"stored status '{(org.get('board') or {}).get('status')}'",
            },
        }
        irs = rec["irs"]
        if irs.get("checked") and irs.get("irs_name"):
            rec["name_overlap"] = name_overlap(org["name"], irs["irs_name"])
        findings.append(rec)
        print(f"  {org['short_name']}", flush=True)
        time.sleep(0.4)
    return findings


def sweep_other_orgs(data):
    """The 12 'Other Rabbit-Friendly Organizations'. These render publicly at
    /other-rescues/ with their `reason` text as the visible description, so the
    reasons are published claims and deserve a read, not just a link check."""
    findings = []
    for org in data["excluded_organizations"]:
        findings.append({
            "section": "excluded_organizations",
            "stored_name": org["name"],
            "published_reason": org.get("reason"),
            "website": {"url": org.get("url"), **check_site(org.get("url"))},
        })
        print(f"  {org['name']}", flush=True)
        time.sleep(0.4)
    return findings


def sweep_closed_orgs(data):
    findings = []
    for org in data["closed_organizations"]:
        findings.append({
            "section": "closed_organizations",
            "stored_name": org["name"],
            "shown_publicly": org.get("show_in_ui"),
            "published_reason": org.get("reason"),
            "website": {"url": org.get("url"), **check_site(org.get("url"))},
        })
        print(f"  {org['name']}", flush=True)
        time.sleep(0.4)
    return findings


def sweep_shelters(data):
    """The 19 shelters and humane societies. Only name + url + region are stored,
    so there is no EIN to check against. The cross-domain redirect check is the
    real detector here: this section is where the HSP/HSTB merger error lived."""
    findings = []
    for org in data["shelters_and_services"]:
        findings.append({
            "section": "shelters_and_services",
            "stored_name": org["name"],
            "region": org.get("region"),
            "website": {"url": org.get("url"), **check_site(org.get("url"))},
        })
        print(f"  {org['name']}", flush=True)
        time.sleep(0.4)
    return findings


def report(findings):
    print("\n--- IRS anomalies (blank = all clean) ---")
    for r in findings:
        irs = r.get("irs")
        if not irs:
            continue
        if not irs.get("checked"):
            print(f"  {r['short_name']}: NOT CHECKED, {irs.get('reason')}")
            continue
        flags = []
        if irs.get("revoke_date"):
            flags.append(f"EXEMPTION REVOKED {irs['revoke_date']}")
        if irs.get("subsection_code") != 3:
            flags.append(f"subsection={irs.get('subsection_code')}")
        if irs.get("state") != "FL":
            flags.append(f"state={irs.get('state')}")
        ov = r.get("name_overlap")
        if ov is not None and ov < NAME_REVIEW_THRESHOLD:
            flags.append(f"NAME {ov}: stored '{r['stored_name']}' "
                         f"vs IRS '{irs['irs_name']}'")
        if flags:
            print(f"  {r['short_name']}: " + "; ".join(flags))

    print("\n--- unreachable sites (blank = all reachable) ---")
    for r in findings:
        w = r["website"]
        if w.get("checked") and w.get("status") != 200:
            print(f"  {r.get('short_name') or r['stored_name']}: "
                  f"{w['status']} {w['url']}")

    print("\n--- cross-domain redirects (the merger detector; blank = none) ---")
    for r in findings:
        note = r["website"].get("redirect_note")
        if note:
            print(f"  {r.get('short_name') or r['stored_name']}: {note}")

    print("\n--- ceased-operation signals (read the context, expect false positives) ---")
    for r in findings:
        for h in r["website"].get("ceased_signals") or []:
            print(f"  {r.get('short_name') or r['stored_name']} [{h['pattern']}]")
            print(f"      ...{h['context']}...")


def main():
    with open(DATA_PATH) as f:
        data = json.load(f)

    print("main directory orgs:")
    findings = sweep_main_orgs(data)
    print("other rabbit-friendly orgs:")
    findings += sweep_other_orgs(data)
    print("shelters and humane societies:")
    findings += sweep_shelters(data)
    print("closed orgs:")
    findings += sweep_closed_orgs(data)

    report(findings)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(findings, f, indent=1)
    print(f"\nwrote {OUT_PATH} ({len(findings)} records)")
    print("Reminder: Sunbiz, Petfinder, and social links remain UNVERIFIED by this sweep.")


if __name__ == "__main__":
    main()
