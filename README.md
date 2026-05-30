# Who Is Not Following Back & Auto Follow/Unfollow 🔍🤖

![GitHub](https://img.shields.io/badge/GitHub-Tool-black) ![Python](https://img.shields.io/badge/Python-3.x-blue) ![License](https://img.shields.io/badge/License-MIT-green)

A Python toolkit that identifies GitHub users who aren't following you back, finds new users likely to follow you back, and automatically manages your following list.

---

## 🙏 Credits

**Base code by Sahil002620Q ** — Original script that identifies users not following back.

**Extended by [Panshul Vempalli](https://github.com/PanshulVempalli)** — Added auto-follow, auto-unfollow, activity tracking, follower categorization, smart filtering, and GitHub Actions automation.

---

## ✨ Features

- 🔍 **Identifies** all users not following you back
- 📊 **Categorizes** users by activity and follower count
- 🔥 **Smart follow** — finds users most likely to follow you back
- ❌ **Auto-unfollow** — unfollows users who didn't follow back after 30 days
- 🤖 **Fully automated** — runs every day via GitHub Actions
- ✅ **Confirmation prompts** — always asks before taking action
- ⚡ **Rate limit protection** — built-in delays to avoid GitHub API limits

---

## 📁 Scripts

| Script | Description |
|--------|-------------|
| `script.py` | Identifies who isn't following you back and optionally unfollows them |
| `who_to_follow.py` | Analyzes users and finds best candidates to follow for follow-backs |
| `auto_follow.py` | Automated daily follow/unfollow script used by GitHub Actions |

---

## 🧠 How It Works

### 🔍 script.py — Who isn't following back?
Scans your following list and compares it to your followers. Shows a breakdown of who isn't following back categorized by:

**Activity:**
| Bucket | Description |
|--------|-------------|
| Active (0-2 weeks) | Recently active |
| 2-4 weeks | Slightly less active |
| 4 weeks-6 months | Moderately inactive |
| 6 months-1 year | Mostly inactive |
| 1 year+ | Likely abandoned |
| Unknown | No activity data |

Then asks you who to unfollow:

Unfollow everyone not following back
Unfollow all inactive users
Unfollow inactive users with under 100 followers
Unfollow users inactive 6 months+ with under 100 followers
Unfollow users inactive for 1 year+
Cancel


### 🔥 who_to_follow.py — Who should I follow?
Scans a source account's followers and analyzes each user based on:
- **Activity** — how recently they were active
- **Follower count** — how big their account is
- **Follow-back ratio** — `following / followers` — higher ratio = more likely to follow back

Then asks you who to follow:

Active (0-2 weeks)
Inactive 2-4 weeks
...
🔥 Likely to follow back
⭐ Best follow-back candidates
...
Cancel


### 🤖 auto_follow.py — Fully Automated
Runs every day via GitHub Actions and:
- **Follows** 100 new users most likely to follow back
- **Unfollows** anyone who didn't follow back after 30 days
- **Saves a log** in `follow_log.json` to track everyone followed and when

---

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- `requests` library

### Installation
```bash
git clone https://github.com/PanshulVempalli/Who-is-not-following-back-git
cd Who-is-not-following-back-git
pip install requests
```

### GitHub Token Setup
1. Go to **github.com/settings/tokens**
2. Click **"Generate new token (classic)"**
3. Check the **`user`** scope
4. Copy the token

---

## 📖 Usage

### CHANGE THE USER 

The algorithm runs on my account ( Panshul Vempalli ) - change it to your username for it to work

### Check who isn't following back:
```bash
GITHUB_TOKEN=your_token python script.py
```

### Unfollow users not following back:
```bash
GITHUB_TOKEN=your_token python script.py --unfollow
```

### Find best users to follow:
```bash
GITHUB_TOKEN=your_token python who_to_follow.py --source torvalds --endpoint followers --limit 100
```

### Run auto follow/unfollow manually:
```bash
GITHUB_TOKEN=your_token python auto_follow.py
```

---

## 🤖 GitHub Actions Automation

The tool runs **automatically every day at 9am** via GitHub Actions:
- Follows 100 new people likely to follow back
- Unfollows anyone who didn't follow back after 30 days

### Setup:
1. Go to repo **Settings → Actions → General**
2. Set **Workflow permissions** to **"Read and write"**
3. Go to **Settings → Secrets → Actions**
4. Add secret: `FOLLOW_TOKEN` = your GitHub token
5. The workflow runs automatically every day!

---

## ⚠️ Important Notes

- **Rate Limiting** — Keep `--limit` under 200 to avoid hitting GitHub's API limit
- **Token Security** — Never share or commit your GitHub token publicly
- **Stay Safe** — Keep follows under 100/day to avoid account flags
- **Use Responsibly** — Excessive automation may violate GitHub's Terms of Service

---

## 🗺️ Roadmap

- [ ] Auto-retry on rate limit with countdown timer
- [ ] Export results to CSV
- [ ] Filter by location or bio keywords
- [ ] Support for organizations
- [ ] Web dashboard to view follow/unfollow stats

---

*Built by [Panshul Vempalli](https://github.com/PanshulVempalli) · Base concept by Sahil002620Q *
