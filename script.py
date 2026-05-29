import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import os
import sys

import requests

username = "PanshulVempalli"
ACTIVITY_WINDOW_DAYS = 14


def get_request_headers(require_token=False):
    headers = {"User-Agent": "Mozilla/5.0"}
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif require_token:
        raise RuntimeError("GitHub token is required for follow/unfollow actions. Set GITHUB_TOKEN or GH_TOKEN.")
    return headers


def fetch_json(url, context):
    response = requests.get(url, headers=get_request_headers(), timeout=30)
    data = response.json()

    if isinstance(data, dict) and "message" in data:
        message = data.get("message", "Unknown API error")
        raise RuntimeError(f"GitHub API error for {context}: {message}")

    if not response.ok:
        raise RuntimeError(f"GitHub API error for {context}: HTTP {response.status_code}")

    return data


def get_all_users(endpoint):
    users = []
    page = 1

    while True:
        url = f"https://api.github.com/users/{username}/{endpoint}?per_page=100&page={page}"
        data = fetch_json(url, endpoint)

        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected GitHub API response for {endpoint}")

        if not data:
            break

        users.extend([user["login"] for user in data if isinstance(user, dict) and "login" in user])
        page += 1

    return set(users)


def unfollow_user(user):
    url = f"https://api.github.com/user/following/{user}"
    response = requests.delete(url, headers=get_request_headers(require_token=True), timeout=30)

    if response.status_code == 204:
        return True
    if response.status_code == 404:
        raise RuntimeError(f"Unable to unfollow {user}: user not found or not currently followed")

    try:
        error = response.json().get("message", None)
    except ValueError:
        error = None

    if not response.ok:
        message = error or f"HTTP {response.status_code}"
        raise RuntimeError(f"GitHub API error for unfollowing {user}: {message}")

    return response.ok


def confirm_action(prompt):
    try:
        return input(f"{prompt} [y/N]: ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def get_inactivity_bucket(last_updated, now=None):
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


def get_user_profile(user):
    url = f"https://api.github.com/users/{user}"
    data = fetch_json(url, user)

    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected GitHub API response for {user}")

    updated_at = data.get("updated_at")
    if not updated_at:
        last_updated = None
        is_active = False
    else:
        last_updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        active_cutoff = datetime.now(timezone.utc) - timedelta(days=ACTIVITY_WINDOW_DAYS)
        is_active = last_updated >= active_cutoff

    follower_count = data.get("followers")
    if follower_count is None:
        follower_count = 0

    return {
        "active": is_active,
        "followers": follower_count,
        "last_updated": last_updated,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find GitHub accounts that do not follow back and optionally unfollow them.")
    parser.add_argument("--unfollow", action="store_true", help="Unfollow accounts that are not following back")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation when unfollowing")
    args = parser.parse_args(argv)

    try:
        following = get_all_users("following")
        followers = get_all_users("followers")

        not_following_back = following - followers

        print(f"Checking activity for {len(not_following_back)} users...")
        profiles = {}
        max_workers = min(3, max(1, len(not_following_back)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_user = {executor.submit(get_user_profile, user): user for user in sorted(not_following_back)}
            completed = 0
            total = len(future_to_user)
            for future in as_completed(future_to_user):
                completed += 1
                user = future_to_user[future]
                profiles[user] = future.result()
                if completed % 100 == 0 or completed == total:
                    print(f"Checked {completed}/{total} users...")

        active_users = [user for user in sorted(not_following_back) if profiles[user]["active"]]
        inactive_users = [user for user in sorted(not_following_back) if not profiles[user]["active"]]

        inactive_buckets = {
            "2-4 weeks": [],
            "4 weeks-6 months": [],
            "6 months-1 year": [],
            "1 year+": [],
            "Unknown": [],
        }
        for user in sorted(not_following_back):
            if profiles[user]["active"]:
                continue
            bucket = get_inactivity_bucket(profiles[user]["last_updated"])
            inactive_buckets.setdefault(bucket, []).append(user)

        below_follower_cap = [user for user in sorted(not_following_back) if profiles[user]["followers"] < 200]
        above_follower_cap = [user for user in sorted(not_following_back) if profiles[user]["followers"] >= 200]

        inactive_over_6_months_under_100 = [
            user
            for user in sorted(not_following_back)
            if profiles[user]["followers"] < 100
            and get_inactivity_bucket(profiles[user]["last_updated"]) in ("6 months-1 year", "1 year+")
        ]

        print(f"\n--- Users not following {username} back ({len(not_following_back)}) ---")
        print(f"Active in the last {ACTIVITY_WINDOW_DAYS} days: {len(active_users)}")
        print(f"Inactive in the last {ACTIVITY_WINDOW_DAYS} days: {len(inactive_users)}")
        print(f"Below 200 followers: {len(below_follower_cap)}")
        print(f"200+ followers: {len(above_follower_cap)}")
        print(f"Inactive more than 6 months and fewer than 100 followers: {len(inactive_over_6_months_under_100)}")

        for label in ["2-4 weeks", "4 weeks-6 months", "6 months-1 year", "1 year+", "Unknown"]:
            bucket_users = inactive_buckets.get(label, [])
            print(f"\n--- {label} ({len(bucket_users)}) ---")
            for user in bucket_users:
                print(f"  {user}: inactive ({profiles[user]['followers']} followers)")

        if args.unfollow:
            print("\n--- Unfollow Options ---")
            print("1. Unfollow everyone not following back")
            print("2. Unfollow all inactive users")
            print("3. Unfollow inactive users with under 100 followers")
            print("4. Unfollow users inactive for 6 months+ with under 100 followers")
            print("5. Unfollow users inactive for 1 year+")
            print("6. Cancel")

            try:
                choice = input("\nChoose an option (1-6): ").strip()
            except EOFError:
                choice = "6"

            if choice == "1":
                targets = sorted(not_following_back)
                label = "everyone not following back"
            elif choice == "2":
                targets = inactive_users
                label = "all inactive users"
            elif choice == "3":
                targets = [u for u in inactive_users if profiles[u]["followers"] < 100]
                label = "inactive users with under 100 followers"
            elif choice == "4":
                targets = inactive_over_6_months_under_100
                label = "users inactive 6+ months with under 100 followers"
            elif choice == "5":
                targets = inactive_buckets.get("1 year+", [])
                label = "users inactive for 1 year+"
            else:
                print("Operation cancelled.")
                return

            if not targets:
                print(f"No users found matching: {label}")
                return

            print(f"\nFound {len(targets)} users to unfollow ({label})")

            if not args.yes and not confirm_action(f"Are you sure you want to unfollow {len(targets)} users?"):
                print("Operation cancelled.")
                return

            print(f"Unfollowing {len(targets)} users...")
            for user in targets:
                try:
                    unfollow_user(user)
                    print(f"Unfollowed {user}")
                except RuntimeError as exc:
                    print(f"Failed to unfollow {user}: {exc}", file=sys.stderr)

            print(f"\nDone! Unfollowed {len(targets)} users.")

    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()