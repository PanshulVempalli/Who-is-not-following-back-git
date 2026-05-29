import os
import sys
import time
import json
import requests
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

username = "PanshulVempalli"
FOLLOW_PER_DAY = 100
UNFOLLOW_AFTER_DAYS = 30
LOG_FILE = "follow_log.json"
SOURCE = "torvalds"


def get_request_headers():
    headers = {"User-Agent": "Mozilla/5.0"}
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        raise RuntimeError("GitHub token required.")
    return headers


def fetch_json(url, context):
    response = requests.get(url, headers=get_request_headers(), timeout=30)
    data = response.json()
    if isinstance(data, dict) and "message" in data:
        raise RuntimeError(f"GitHub API error for {context}: {data.get('message')}")
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status_code} for {context}")
    return data


def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def get_my_following():
    users = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/following?per_page=100&page={page}"
        data = fetch_json(url, "following")
        if not data:
            break
        users.extend([u["login"] for u in data if isinstance(u, dict)])
        page += 1
    return set(users)


def get_my_followers():
    users = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/followers?per_page=100&page={page}"
        data = fetch_json(url, "followers")
        if not data:
            break
        users.extend([u["login"] for u in data if isinstance(u, dict)])
        page += 1
    return set(users)


def get_candidates(source, limit=300):
    users = []
    page = 1
    while len(users) < limit:
        url = f"https://api.github.com/users/{source}/followers?per_page=100&page={page}"
        data = fetch_json(url, source)
        if not data:
            break
        users.extend([u["login"] for u in data if isinstance(u, dict)])
        page += 1
    return users[:limit]


def get_user_profile(user):
    url = f"https://api.github.com/users/{user}"
    data = fetch_json(url, user)
    followers = data.get("followers", 0)
    following = data.get("following", 0)
    updated_at = data.get("updated_at")

    if updated_at:
        last_updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        active_cutoff = datetime.now(timezone.utc) - timedelta(days=60)
        is_active = last_updated >= active_cutoff
    else:
        is_active = False

    likely_follow_back = following >= followers and following > 0

    return {
        "active": is_active,
        "followers": followers,
        "following": following,
        "likely_follow_back": likely_follow_back,
    }


def follow_user(user):
    url = f"https://api.github.com/user/following/{user}"
    response = requests.put(url, headers=get_request_headers(), timeout=30)
    return response.status_code == 204


def unfollow_user(user):
    url = f"https://api.github.com/user/following/{user}"
    response = requests.delete(url, headers=get_request_headers(), timeout=30)
    return response.status_code == 204


def main():
    log = load_log()
    now = datetime.now(timezone.utc)

    print("Fetching your followers and following...")
    already_following = get_my_following()
    my_followers = get_my_followers()
    print(f"Following: {len(already_following)} | Followers: {len(my_followers)}")

    # --- Step 1: Unfollow people who didn't follow back after 30 days ---
    to_unfollow = []
    for user, data in log.items():
        if data.get("unfollowed"):
            continue
        followed_at = datetime.fromisoformat(data["followed_at"])
        days_since = (now - followed_at).days
        if days_since >= UNFOLLOW_AFTER_DAYS and user not in my_followers:
            to_unfollow.append(user)

    if to_unfollow:
        print(f"\nUnfollowing {len(to_unfollow)} users who didn't follow back after {UNFOLLOW_AFTER_DAYS} days...")
        for i, user in enumerate(to_unfollow, 1):
            try:
                if unfollow_user(user):
                    print(f"[{i}/{len(to_unfollow)}] Unfollowed {user}")
                    log[user]["unfollowed"] = True
                    log[user]["unfollowed_at"] = now.isoformat()
            except Exception as exc:
                print(f"Failed to unfollow {user}: {exc}")
            time.sleep(0.5)
    else:
        print("\nNo users to unfollow today.")

    # --- Step 2: Follow new users ---
    print(f"\nFetching candidates from {SOURCE}...")
    candidates = get_candidates(SOURCE, limit=500)
    candidates = [
        u for u in candidates
        if u not in already_following
        and u not in log
        and u != username
    ]
    print(f"Found {len(candidates)} new candidates")

    print(f"Analyzing candidates...")
    profiles = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_user = {executor.submit(get_user_profile, user): user for user in candidates[:200]}
        for future in as_completed(future_to_user):
            user = future_to_user[future]
            try:
                profiles[user] = future.result()
            except RuntimeError:
                profiles[user] = None
            time.sleep(0.2)

    # Filter best candidates
    best = [
        u for u, p in profiles.items()
        if p and p["active"] and p["likely_follow_back"] and p["followers"] < 500
    ]

    # Fall back to active users if not enough best candidates
    if len(best) < FOLLOW_PER_DAY:
        active = [
            u for u, p in profiles.items()
            if p and p["active"] and u not in best
        ]
        best += active

    targets = best[:FOLLOW_PER_DAY]

    if not targets:
        print("No suitable candidates found today.")
        save_log(log)