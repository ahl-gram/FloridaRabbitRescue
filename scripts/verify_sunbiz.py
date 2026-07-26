"""Verify directory listings against Florida's official corporate registry.

Run:  python3 scripts/verify_sunbiz.py

Kept separate from verify.py on purpose. verify.py is self-contained and needs only a
network connection; this script needs a 1.82 GB bulk data file that most people will not
have. It skips cleanly with instructions when the file is absent, and never downloads
anything itself.

WHY THIS EXISTS
    An organization's website returning HTTP 200 is not evidence the organization still
    exists. Two errors reached the live site before this check existed:
      - Humane Society of Pinellas merged into HSTB in Jan 2026; its URL kept returning 200.
      - Fort Wilbur filed a VOLUNTARY DISSOLUTION in Apr 2026 with a live website and
        unrevoked IRS exempt status.
    The state corporate registry is the authority that catches both.

GETTING THE DATA (public, no account or API key)
    The login below is NOT a secret. It is the anonymous public-access credential that the
    Florida Department of State publishes for this dataset, documented at
    https://dos.fl.gov/sunbiz/other-services/data-downloads/ - the equivalent of an
    anonymous FTP login. It grants read-only access to already-public bulk records.

    You must run this download by hand, in a real terminal. It cannot be scripted here:
    macOS system curl is built without SFTP support (check with `curl -V`), and only the
    interactive sftp client is available, which needs a TTY for the password prompt. If you
    are working with an AI assistant, expect it to be unable to do this step for you.

    sftp Public@sftp.floridados.gov          password: PubAccess1845!
    sftp> cd doc/quarterly/cor
    sftp> lcd /absolute/path/to/repo/planning/sunbiz
    sftp> get cordata.zip                    1.82 GB, corporate filings + status
    sftp> get corevent.zip                   189 MB, the events explaining WHY inactive
    sftp> bye

    Use an ABSOLUTE path for lcd. It resolves against the directory you launched sftp from,
    so a relative path silently deposits the files somewhere unexpected.

    Verify the transfer completed by comparing byte sizes against the `ls -l` output on the
    server. A truncated zip fails late and confusingly.

    Regenerated each January, April, July, and October. Check the server-side file date: if
    it predates the current quarter you are reading stale registry data, and should say so
    rather than let the output look current.

    Do NOT unzip these. Uncompressed they are about 18.5 GB. This script streams them,
    and a full scan of all 12.8 million records takes roughly 20 seconds.

    Note the docs describe the corporate data as "broken into 10 smaller files" in a way
    that reads as if they are separate downloads. They are not. There is one cordata.zip,
    and the ten files (cordata0.txt .. cordata9.txt) are inside it, partitioned by the LAST
    DIGIT of the document number. corevent.zip holds a single corevt.txt.

RECORD LAYOUT
    Verified against real records. The official field definitions are 1-indexed, so every
    documented "start" position is one greater than the Python slice index used here.
    cordata: 1442 bytes per record = 1440 payload + CRLF
    corevt : 664 bytes per record = 662 payload + CRLF
    Full field table, including the ones this script does not read, is in
    planning/verification-2026-07.md.

WHEN ADDING A NEW ORGANIZATION: the trailing-digit trap
    Sunbiz's own result URLs append a sequence digit to the document number, so the URL for
    N04000003455 contains N040000034550 (13 characters). A real document number is 12
    characters: N plus 11 digits. Copying from the URL silently produces an unmatchable
    value, and these render publicly on /directory/ as linked "Sunbiz:" text. Three listings
    shipped with this error. Take the first 12 characters, and confirm the number matches a
    registry record before trusting it.

IF YOU CHANGE THE PARSING, RE-VALIDATE FIRST
    Fixed-width offset math fails silently: a one-byte shift yields plausible garbage rather
    than an exception, so a clean-looking run proves nothing. Before trusting any change,
    read back a record whose answer is known independently. Two that work today:
      - N04000011513 (H.A.R.E.) must report file date 12102004. That date came from separate
        research recorded in its founded_source, so it is a genuine external check.
      - N23000014374 (Happy Bunny Rescue) must report status I with last transaction
        09272024, matching the closure our data already documents.
    A verification tool reporting "nothing found" is indistinguishable from a broken one.

WHAT THIS DOES NOT TELL YOU
    Registry status is about the legal entity, not the rescue. An organization can keep
    taking rabbits after dissolving its corporation, and can stay registered long after it
    stops operating. Status I is grounds to make contact, never grounds to silently
    reclassify a listing. Both real findings here were confirmed with a human before the
    site changed.
"""

import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
DATA_PATH = os.path.join(ROOT, "directory-data.json")
SUNBIZ_DIR = os.path.join(ROOT, "planning", "sunbiz")
CORDATA_ZIP = os.path.join(SUNBIZ_DIR, "cordata.zip")
COREVENT_ZIP = os.path.join(SUNBIZ_DIR, "corevent.zip")

CORDATA_RECORD, CORDATA_PAYLOAD = 1442, 1440
COREVENT_RECORD, COREVENT_PAYLOAD = 664, 662

# 0-indexed slices. Subtract 1 from the "start" column in the official definitions.
COR = {
    "doc_number": (0, 12),
    "name": (12, 192),
    "status": (204, 1),
    "filing_type": (205, 15),
    "file_date": (472, 8),
    "last_tx_date": (495, 8),
}
EVT = {
    "doc_number": (0, 12),
    "code": (17, 20),
    "description": (37, 48),
    "filed_date": (85, 8),
}

DOC_NUMBER_RE = re.compile(r"N\d{11}")
NONPROFIT_FILING_TYPE = "DOMNP"
DISCOVERY_KEYWORDS = (b"RABBIT", b"BUNNY", b"LAGOMORPH")

# Words too generic to distinguish one rabbit rescue from another.
MATCH_STOPWORDS = {
    "inc", "incorporated", "corporation", "corp", "of", "the", "a", "and",
    "fl", "florida", "rescue", "rescues", "rabbit", "rabbits", "bunny",
    "bunnies", "sanctuary",
}
ALREADY_LISTED = 0.5
POSSIBLE_MATCH = 0.25


def field(record, spec):
    start, length = spec
    return record[start:start + length]


def text(record, spec):
    return field(record, spec).strip()


def fmt_date(raw):
    raw = raw.strip()
    return f"{raw[0:2]}/{raw[2:4]}/{raw[4:8]}" if len(raw) == 8 else "-"


def tokens(name):
    words = re.findall(r"[a-z]+", (name or "").lower())
    return {w for w in words if w not in MATCH_STOPWORDS}


def overlap(a, b):
    ta, tb = tokens(a), tokens(b)
    if not (ta or tb):
        return 0.0
    return len(ta & tb) / len(ta | tb)


def iter_records(zip_path, record_len, payload_len, members=None):
    """Stream fixed-width records without expanding the archive to disk."""
    with zipfile.ZipFile(zip_path) as archive:
        names = members or sorted(i.filename for i in archive.infolist())
        for member in names:
            with archive.open(member) as handle:
                buf = b""
                while True:
                    chunk = handle.read(record_len * 8000)
                    if not chunk:
                        break
                    buf += chunk
                    usable = len(buf) - (len(buf) % record_len)
                    for off in range(0, usable, record_len):
                        yield buf[off:off + payload_len].decode("latin-1")
                    buf = buf[usable:]


def doc_number_of(org):
    """Stored document number, falling back to the one embedded in sunbiz_url.

    Closed organizations have no sunbiz_document_number field, but their
    sunbiz_url contains the number with an extra trailing digit appended by
    Sunbiz's own URL format.
    """
    nonprofit = org.get("nonprofit") or {}
    stored = nonprofit.get("sunbiz_document_number")
    if stored:
        return stored[:12]
    for url in (nonprofit.get("sunbiz_url"), org.get("sunbiz_url")):
        match = DOC_NUMBER_RE.search(url or "")
        if match:
            return match.group(0)
    return None


def load_targets(data):
    """Map document number -> (label, display name) for every org we can check."""
    targets = {}
    for section, label in (("organizations", "listed"),
                           ("closed_organizations", "closed")):
        for org in data.get(section, []):
            number = doc_number_of(org)
            if number:
                name = org.get("short_name") or org["name"]
                targets[number] = (label, name, org["name"])
    return targets


def known_names(data):
    names = []
    for section in ("organizations", "excluded_organizations",
                    "closed_organizations", "shelters_and_services"):
        names.extend(o["name"] for o in data.get(section, []))
    return names


def scan_corporate(targets, known):
    """One pass over the registry: match our orgs, and discover unlisted rescues."""
    matched, discovered = {}, []
    scanned = 0
    for record in iter_records(CORDATA_ZIP, CORDATA_RECORD, CORDATA_PAYLOAD):
        scanned += 1
        number = field(record, COR["doc_number"])
        if number in targets:
            matched[number] = record
            continue
        if text(record, COR["status"]) != "A":
            continue
        if text(record, COR["filing_type"]) != NONPROFIT_FILING_TYPE:
            continue
        raw_name = field(record, COR["name"]).encode("latin-1")
        if any(kw in raw_name for kw in DISCOVERY_KEYWORDS):
            discovered.append(record)
    return matched, discovered, scanned


def scan_events(numbers):
    events = {}
    if not os.path.exists(COREVENT_ZIP):
        return None
    for record in iter_records(COREVENT_ZIP, COREVENT_RECORD, COREVENT_PAYLOAD):
        number = field(record, EVT["doc_number"])
        if number in numbers:
            events.setdefault(number, []).append(record)
    return events


def report_status(targets, matched):
    print("\n== Registry status ==")
    inactive, missing = [], []
    for number, (kind, label, _) in sorted(targets.items(), key=lambda x: x[1][1]):
        record = matched.get(number)
        if record is None:
            missing.append((label, number))
            continue
        status = text(record, COR["status"])
        note = ""
        if kind == "listed" and status != "A":
            note = "   <== LISTED BUT NOT ACTIVE"
            inactive.append((label, number))
        elif kind == "closed" and status == "A":
            note = "   <== listed as closed but registry says active"
        print(f"  {status}  {number}  filed {fmt_date(text(record, COR['file_date']))}"
              f"  {label[:30]:<30}{note}")
    if missing:
        print("\n  not found in registry:")
        for label, number in missing:
            print(f"    {label} ({number})")
    return inactive


def report_events(events, targets, focus):
    if events is None:
        print(f"\n== Events ==\n  skipped, {COREVENT_ZIP} not present")
        return
    print("\n== Events for organizations needing explanation ==")
    if not focus:
        print("  none flagged")
        return
    for label, number in focus:
        print(f"  {label} ({number})")
        for record in events.get(number, []):
            desc = " ".join(text(record, EVT["description"]).split())
            print(f"    {fmt_date(text(record, EVT['filed_date']))}  {desc}")


def report_discovered(discovered, known):
    print("\n== Active FL rabbit/bunny nonprofits not in the directory ==")
    print("  Names only, unresearched. Exact-name dedup does NOT work here: registry legal")
    print("  names are longer than display names, so this uses token overlap. Verify each.")
    rows = []
    for record in discovered:
        name = text(record, COR["name"])
        best_score, best_name = max(
            ((overlap(name, known_name), known_name) for known_name in known),
            default=(0.0, ""))
        if best_score >= ALREADY_LISTED:
            continue
        hint = f"possible match: {best_name}" if best_score >= POSSIBLE_MATCH else ""
        rows.append((name, text(record, COR["doc_number"]),
                     fmt_date(text(record, COR["file_date"])), hint))
    if not rows:
        print("  none")
    for name, number, filed, hint in sorted(rows):
        print(f"  {number}  filed {filed}  {name[:44]:<44} {hint}")
    return rows


def missing_data_message():
    print(f"Bulk registry data not found at {SUNBIZ_DIR}")
    print("\nThis check needs Florida's public corporate data. To fetch it:")
    print("    sftp Public@sftp.floridados.gov      password: PubAccess1845!")
    print("    sftp> cd doc/quarterly/cor")
    print(f"    sftp> lcd {SUNBIZ_DIR}")
    print("    sftp> get cordata.zip")
    print("    sftp> get corevent.zip")
    print("\nSee the module docstring for details. Skipping.")


def main():
    if not os.path.exists(CORDATA_ZIP):
        missing_data_message()
        return 0

    with open(DATA_PATH) as f:
        data = json.load(f)

    targets = load_targets(data)
    known = known_names(data)
    print(f"checking {len(targets)} organizations against the FL corporate registry")

    matched, discovered, scanned = scan_corporate(targets, known)
    print(f"scanned {scanned:,} records, matched {len(matched)} of {len(targets)}")

    inactive = report_status(targets, matched)
    events = scan_events(set(targets))
    report_events(events, targets, inactive)
    rows = report_discovered(discovered, known)

    print("\n== Summary ==")
    if inactive:
        print(f"  {len(inactive)} listed org(s) NOT active in the registry. Contact them")
        print("  before changing any listing: a dissolved corporation does not by itself")
        print("  prove an organization stopped taking rabbits.")
    else:
        print("  all listed organizations are active in the registry")
    print(f"  {len(rows)} candidate rescue(s) not currently in the directory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
