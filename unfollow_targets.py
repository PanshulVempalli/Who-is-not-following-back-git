#!/usr/bin/env python3
"""
Safely unfollow GitHub users who are not following back, have <100 followers,
and have been inactive >6 months.

Usage:
  GITHUB_TOKEN=<token> python unfollow_targets.py [--yes]

This script will:
- Fetch following and followers lists for the configured username
- Identify targets (followers <100 and inactive >6 months)
- Prompt for confirmation (unless --yes) and unfollow each target, logging results
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

USERNAME = "PanshulVempalli"


def get_headers(require_token=False):
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    headers = {"User-Agent": "Mozilla/5.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif require_token:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN required to perform follow actions")
    return headers


def fetch_paginated_users(endpoint):
    users = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USERNAME}/{endpoint}?per_page=100&page={page}"
        r = requests.get(url, headers=get_headers(), timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        users.extend([u["login"] for u in data if isinstance(u, dict) and "login" in u])
        page += 1
    return users


def get_profile(user):
    r = requests.get(f"https://api.github.com/users/{user}", headers=get_headers(), timeout=30)
    r.raise_for_status()
    data = r.json()
    updated_at = data.get("updated_at")
    last_updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00")) if updated_at else None
    return {"login": data.get("login"), "followers": data.get("followers", 0), "last_updated": last_updated}


def unfollow(user):
    r = requests.delete(f"https://api.github.com/user/following/{user}", headers=get_headers(require_token=True), timeout=30)
    if r.status_code == 204:
        return True, None
    msg = None
    try:
        msg = r.json().get("message")
    except Exception:
        msg = r.text[:200]
    return False, f"{r.status_code}: {msg}"


def inactivity_bucket(last_updated, now=None):
    if now is None:
        now = datetime.now(timezone.utc)
    if last_updated is None:
        return "Unknown"
    age = now - last_updated
    if age < timedelta(days=14):
        return None
    if age < timedelta(days=28):
        return "2-4 weeks"
    if age < timedelta(days=180):
        return "4 weeks-6 months"
    if age < timedelta(days=365):
        return "6 months-1 year"
    return "1 year+"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="Skip confirmation")
    args = parser.parse_args(argv)

    print(f"Fetching following/followers for {USERNAME}...")
    following = fetch_paginated_users("following")
    followers = fetch_paginated_users("followers")

    not_following_back = sorted(set(following) - set(followers))
    print(f"Found {len(not_following_back)} accounts not following back")

    now = datetime.now(timezone.utc)
    targets = []
    for i, user in enumerate(not_following_back, start=1):
        try:
            profile = get_profile(user)
        except Exception as e:
            print(f"Skipping {user}: profile error {e}")
            continue
        bucket = inactivity_bucket(profile["last_updated"], now=now)
        if profile["followers"] < 100 and bucket in ("6 months-1 year", "1 year+"):
            targets.append(profile["login"])
        if i % 200 == 0:
            print(f"Checked {i}/{len(not_following_back)} profiles")

    print(f"Targets to unfollow: {len(targets)}")
    if not targets:
        return

    if not args.yes:
        ok = input(f"Really unfollow {len(targets)} users from account {USERNAME}? [y/N]: ").strip().lower()
        if ok not in ("y", "yes"):
            print("Aborting.")
            return

    results = []
    for idx, user in enumerate(targets, start=1):
        try:
            success, err = unfollow(user)
            if success:
                print(f"[{idx}/{len(targets)}] Unfollowed {user}")
                results.append({"user": user, "status": "unfollowed"})
            else:
                print(f"[{idx}/{len(targets)}] Failed {user}: {err}")
                results.append({"user": user, "status": "failed", "message": err})
        except Exception as e:
            print(f"[{idx}/{len(targets)}] Error {user}: {e}")
            results.append({"user": user, "status": "error", "message": str(e)})
        time.sleep(0.2)

    with open("unfollow_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Done. Results written to unfollow_results.json")


if __name__ == "__main__":
    main()
