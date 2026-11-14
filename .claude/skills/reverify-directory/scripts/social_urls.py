"""Print "label<TAB>url" for every main-directory social, Linktree and adoption-listing URL.

usage: python3 social_urls.py [facebook|instagram|tiktok|linktree|listing ...] > urls.tsv
With no arguments, prints every kind. Labels are "<org id>:<kind>".
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[os.pardir] * 4))


def rows(data):
    for org in data["organizations"]:
        for kind, url in (org.get("social") or {}).items():
            yield org["id"], kind, url
        if org.get("linktree_url"):
            yield org["id"], "linktree", org["linktree_url"]
        if org.get("adoption_listing_url"):
            yield org["id"], "listing", org["adoption_listing_url"]


def main(kinds):
    with open(os.path.join(ROOT, "directory-data.json")) as f:
        data = json.load(f)
    for org_id, kind, url in rows(data):
        if not kinds or kind in kinds:
            print(f"{org_id}:{kind}\t{url}")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
