import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import os
import sys
import time

import requests

username = "PanshulVempalli"
ACTIVITY_WINDOW_DAYS = 60  # 2 months


def get_request_headers():
    headers = {"User-Agent": "Mozilla/5.0"}
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        raise RuntimeError("GitHub token required. Set GITHUB_TOKEN or GH_TOKEN.")
    return headers


def fetch_json(url, context):
    response = requests.get(url, headers=get_request_headers(), timeout=30)
    data = response.json()
    if isinstance(data, dict) and "message" in data:
        raise RuntimeError(f"GitHub API error for {context}: {data.get('message')}")
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status_code} for {context}")
    return data


def get_my_following():
    users = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/following?per_page5000&page={page}"
        data = fetch_json(url, "following")
        if not data:
            break
        users.extend([u["login"] for u in data if isinstance(u, dict)])
        page += 1
    return set(users)


def get_candidates(source, endpoint, limit=500):
    users = []
    page = 1
    while len(users) < limit:
        url = f"https://api.github.com/users/{source}/{endpoint}?per_page=100&page={page}"
        data = fetch_json(url, source)
        if not data:
            break
        users.extend([u["login"] for u in data if isinstance(u, dict)])
        page += 1
    return users[:limit]


def get_user_profile(user):
    url = f"https://api.github.com/users/{user}"
    data = fetch_json(url, user)

    updated_at = data.get("updated_at")
    if updated_at:
        last_updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        active_cutoff = datetime.now(timezone.utc) - timedelta(days=ACTIVITY_WINDOW_DAYS)
        is_active = last_updated >= active_cutoff
        age = datetime.now(timezone.utc) - last_updated
        if age < timedelta(days=14):
            bucket = "Active (0-2 weeks)"
        elif age < timedelta(days=28):
            bucket = "2-4 weeks"
        elif age < timedelta(days=60):
            bucket = "2-4 weeks"
        elif age < timedelta(days=180):
            bucket = "4 weeks-6 months"
        elif age < timedelta(days=365):
            bucket = "6 months-1 year"
        else:
            bucket = "1 year+"
    else:
        last_updated = None
        is_active = False
        bucket = "Unknown"

    followers = data.get("followers", 0)
    following = data.get("following", 0)

    # Key metric — do they follow more than follow them?
    likely_to_follow_back = following >= followers and following > 0

    if followers == 0:
        follow_back_ratio = following
    else:
        follow_back_ratio = round(following / followers, 2)

    return {
        "active": is_active,
        "followers": followers,
        "following": following,
        "follow_back_ratio": follow_back_ratio,
        "likely_to_follow_back": likely_to_follow_back,
        "bucket": bucket,
    }


def follow_user(user):
    url = f"https://api.github.com/user/following/{user}"
    response = requests.put(url, headers=get_request_headers(), timeout=30)
    return response.status_code == 204


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, default=username)
    parser.add_argument("--endpoint", type=str, default="followers", choices=["followers", "following"])
    parser.add_argument("--limit", type=int, default=2000)
    args = parser.parse_args()

    print(f"Fetching your current following list...")
    already_following = get_my_following()
    print(f"You currently follow {len(already_following)} users\n")

    print(f"Fetching candidates from {args.source}'s {args.endpoint}...")
    candidates = get_candidates(args.source, args.endpoint, args.limit)
    candidates = [u for u in candidates if u not in already_following and u != username]
    print(f"Found {len(candidates)} candidates you don't already follow\n")

    print(f"Analyzing {len(candidates)} users...")
    profiles = {}
    with ThreadPoolExecutor(max_workers=1) as executor:
        future_to_user = {executor.submit(get_user_profile, user): user for user in candidates}
        completed = 0
        total = len(future_to_user)
        for future in as_completed(future_to_user):
            completed += 1
            user = future_to_user[future]
            try:
                profiles[user] = future.result()
            except RuntimeError:
                profiles[user] = None
            if completed % 50 == 0 or completed == total:
                print(f"Analyzed {completed}/{total} users...")
            time.sleep(1)

    valid = {u: p for u, p in profiles.items() if p is not None}

    # --- Activity buckets ---
    activity_buckets = {
        "Active (0-2 weeks)": [],
        "2-4 weeks": [],
        "4 weeks-6 months": [],
        "6 months-1 year": [],
        "1 year+": [],
        "Unknown": [],
    }
    for user, p in valid.items():
        activity_buckets[p["bucket"]].append(user)

    # --- Follower groups ---
    under_100 = [u for u, p in valid.items() if p["followers"] < 100]
    between_100_500 = [u for u, p in valid.items() if 100 <= p["followers"] < 500]
    between_500_1000 = [u for u, p in valid.items() if 500 <= p["followers"] < 1000]
    over_1000 = [u for u, p in valid.items() if p["followers"] >= 1000]

    # --- Follow-back groups ---
    likely_follow_back = [
        u for u, p in valid.items()
        if p["likely_to_follow_back"] and p["active"]
    ]

    best = [
        u for u, p in valid.items()
        if p["active"]
        and p["likely_to_follow_back"]
        and p["followers"] < 500
        and p["following"] > 10
    ]

    good = [
        u for u, p in valid.items()
        if p["active"]
        and p["follow_back_ratio"] >= 0.5
        and p["followers"] < 1000
    ]

    active_small = [
        u for u, p in valid.items()
        if p["active"] and p["followers"] < 100
    ]

    # --- Print results ---
    print(f"\n{'='*55}")
    print(f"📊 ANALYSIS — {len(valid)} users analyzed")
    print(f"{'='*55}")

    print(f"\n📅 Activity Breakdown:")
    for label, users in activity_buckets.items():
        print(f"   {label}: {len(users)}")

    print(f"\n👥 Follower Breakdown:")
    print(f"   Under 100 followers:    {len(under_100)}")
    print(f"   100-500 followers:      {len(between_100_500)}")
    print(f"   500-1000 followers:     {len(between_500_1000)}")
    print(f"   1000+ followers:        {len(over_1000)}")

    print(f"\n🎯 Follow-Back Likelihood:")
    print(f"   ⭐ Best  (active, following >= followers, <500):  {len(best)}")
    print(f"   ✅ Good  (active, ratio >=0.5, <1000 followers): {len(good)}")
    print(f"   🔥 Likely to follow back (active, following >= followers): {len(likely_follow_back)}")
    print(f"   📌 Active + under 100 followers:                 {len(active_small)}")

    # --- Ask who to follow ---
    print(f"\n{'='*55}")
    print(f"Who do you want to follow?")
    print(f"{'='*55}")
    print(f"1.  Active (0-2 weeks)                    ({len(activity_buckets['Active (0-2 weeks)'])} users)")
    print(f"2.  Inactive 2-4 weeks                    ({len(activity_buckets['2-4 weeks'])} users)")
    print(f"3.  Inactive 4 weeks-6 months             ({len(activity_buckets['4 weeks-6 months'])} users)")
    print(f"4.  Inactive 6 months-1 year              ({len(activity_buckets['6 months-1 year'])} users)")
    print(f"5.  Inactive 1 year+                      ({len(activity_buckets['1 year+'])} users)")
    print(f"6.  Under 100 followers                   ({len(under_100)} users)")
    print(f"7.  100-500 followers                     ({len(between_100_500)} users)")
    print(f"8.  500-1000 followers                    ({len(between_500_1000)} users)")
    print(f"9.  1000+ followers                       ({len(over_1000)} users)")
    print(f"10. 🔥 Likely to follow back              ({len(likely_follow_back)} users)")
    print(f"11. ⭐ Best follow-back candidates        ({len(best)} users)")
    print(f"12. ✅ Good follow-back candidates        ({len(good)} users)")
    print(f"13. 📌 Active + under 100 followers       ({len(active_small)} users)")
    print(f"14. Everyone                              ({len(valid)} users)")
    print(f"15. Cancel")

    try:
        choice = input("\nChoose an option (1-15): ").strip()
    except EOFError:
        choice = "15"

    option_map = {
        "1":  (activity_buckets["Active (0-2 weeks)"], "active users"),
        "2":  (activity_buckets["2-4 weeks"], "inactive 2-4 weeks"),
        "3":  (activity_buckets["4 weeks-6 months"], "inactive 4 weeks-6 months"),
        "4":  (activity_buckets["6 months-1 year"], "inactive 6 months-1 year"),
        "5":  (activity_buckets["1 year+"], "inactive 1 year+"),
        "6":  (under_100, "under 100 followers"),
        "7":  (between_100_500, "100-500 followers"),
        "8":  (between_500_1000, "500-1000 followers"),
        "9":  (over_1000, "1000+ followers"),
        "10": (likely_follow_back, "likely to follow back"),
        "11": (best, "best follow-back candidates"),
        "12": (good, "good follow-back candidates"),
        "13": (active_small, "active under 100 followers"),
        "14": (list(valid.keys()), "everyone"),
    }

    if choice not in option_map:
        print("Cancelled.")
        return

    targets, label = option_map[choice]

    if not targets:
        print(f"No users found in this group.")
        return

    print(f"\nFound {len(targets)} users to follow ({label})")

    try:
        confirm = input(f"Are you sure you want to follow {len(targets)} users? [y/N]: ").strip().lower()
    except EOFError:
        confirm = "n"

    if confirm not in ("y", "yes"):
        print("Cancelled.")
        return

    print(f"Following {len(targets)} users...")
    success = 0
    for i, user in enumerate(targets, 1):
        try:
            if follow_user(user):
                print(f"[{i}/{len(targets)}] Followed {user}")
                success += 1
            else:
                print(f"[{i}/{len(targets)}] Failed {user}")
        except Exception as exc:
            print(f"[{i}/{len(targets)}] Error {user}: {exc}")
        time.sleep(0.5)

    print(f"\nDone! Successfully followed {success}/{len(targets)} users.")


if __name__ == "__main__":
    main()