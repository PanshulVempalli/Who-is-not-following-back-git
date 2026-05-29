 Who To Follow 🎯

![GitHub](https://img.shields.io/badge/GitHub-Tool-black) ![Python](https://img.shields.io/badge/Python-3.x-blue) ![License](https://img.shields.io/badge/License-MIT-green)

A smart Python tool that analyzes GitHub users and helps you find people who are **most likely to follow you back** — based on their activity, follower count, and follow-back ratio.

---

## 🙏 Credits

**Base concept and code by [Urvish L.](https://github.com/urvish)** — Original script that identifies users not following back.

**Extended by [Panshul Vempalli](https://github.com/PanshulVempalli)** — Added follow-back likelihood analysis, activity tracking, follower categorization, smart filtering, and auto-follow functionality.

---

## ✨ Features

- 📅 **Activity breakdown** — categorizes users by how recently they were active
- 👥 **Follower breakdown** — splits users by follower count
- 🔥 **Follow-back likelihood** — identifies users most likely to follow you back
- ⭐ **Smart filtering** — finds users where `following >= followers` (they follow back a lot)
- 🤖 **Auto-follow** — follow your chosen group automatically
- ✅ **Confirmation prompt** — always asks before following anyone
- ⚡ **Rate limit protection** — built-in delays to avoid GitHub API limits

---

## 🧠 How It Works

The tool pulls a list of candidate users from a source account (e.g. your own followers, or a popular account's followers). It then analyzes each candidate and sorts them into groups based on:

### 📅 Activity
| Bucket | Description |
|--------|-------------|
| Active (0-2 weeks) | Recently active — most likely to engage |
| 2-4 weeks | Slightly less active |
| 4 weeks-6 months | Moderately inactive |
| 6 months-1 year | Mostly inactive |
| 1 year+ | Likely abandoned account |
| Unknown | No activity data available |

### 👥 Follower Count
| Group | Range |
|-------|-------|
| Small | Under 100 followers |
| Medium | 100-500 followers |
| Large | 500-1000 followers |
| Big | 1000+ followers |

### 🎯 Follow-Back Likelihood
The key metric is the **follow-back ratio**:
follow_back_ratio = following / followers
- A ratio **≥ 1.0** means they follow more people than follow them → **very likely to follow back**
- A ratio **≥ 0.5** means they follow a decent amount → **likely to follow back**
- A ratio **< 0.3** means they are selective → **unlikely to follow back**

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

You need a GitHub Personal Access Token with `user:follow` scope:

1. Go to **github.com/settings/tokens**
2. Click **"Generate new token (classic)"**
3. Check the **`user`** scope
4. Copy the generated token

---

## 📖 Usage

### Basic usage (scan your own followers):
```bash
GITHUB_TOKEN=your_token python who_to_follow.py
```

### Scan a specific account's followers:
```bash
GITHUB_TOKEN=your_token python who_to_follow.py --source torvalds --endpoint followers --limit 100
```

### Scan a specific account's following list:
```bash
GITHUB_TOKEN=your_token python who_to_follow.py --source PanshulVempalli --endpoint following --limit 100
```

### Arguments
| Argument | Default | Description |
|----------|---------|-------------|
| `--source` | Your username | Account to pull candidates from |
| `--endpoint` | `followers` | Use `followers` or `following` list |
| `--limit` | `100` | Number of candidates to analyze |

---

## 📊 Output Example
Fetching your current following list...
You currently follow 1200 users
Fetching candidates from PanshulVempalli's followers...
Found 87 candidates you don't already follow
Analyzing 87 users...
Analyzed 50/87 users...
Analyzed 87/87 users...
=======================================================
📊 ANALYSIS — 87 users analyzed
📅 Activity Breakdown:
Active (0-2 weeks):    34
2-4 weeks:             12
4 weeks-6 months:      18
6 months-1 year:        9
1 year+:                8
Unknown:                6
👥 Follower Breakdown:
Under 100 followers:   45
100-500 followers:     28
500-1000 followers:     8
1000+ followers:        6
🎯 Follow-Back Likelihood:
⭐ Best  (active, following >= followers, <500):   23
✅ Good  (active, ratio >=0.5, <1000 followers):  31
🔥 Likely to follow back (active, following >= followers): 28
📌 Active + under 100 followers:                  19
=======================================================
Who do you want to follow?

Active (0-2 weeks)                    (34 users)
Inactive 2-4 weeks                    (12 users)
...
🔥 Likely to follow back              (28 users)
⭐ Best follow-back candidates        (23 users)
...
Cancel

Choose an option (1-15): 11
Found 23 users to follow (best follow-back candidates)
Are you sure you want to follow 23 users? [y/N]: y
Following 23 users...
[1/23] Followed user123
[2/23] Followed user456
...
Done! Successfully followed 23/23 users.

---

## ⚠️ Important Notes

- **Rate Limiting** — GitHub allows 5000 API requests per hour with a token. Keep `--limit` under 200 to stay safe.
- **Token Security** — Never share or commit your GitHub token publicly.
- **Best Source** — Using your own followers as the source gives the best results since they're already interested in your profile.
- **Use Responsibly** — Avoid running this too frequently to stay within GitHub's Terms of Service.

---

## 💡 Pro Tips

- Use `--limit 50` to stay well within rate limits
- Best source accounts to scan: your own followers, or accounts in your area of interest
- Always use option **10 or 11** for highest follow-back chance
- Run once a day for best results without hitting rate limits

---

## 🗺️ Roadmap

- [ ] Auto-retry on rate limit with countdown timer
- [ ] Export results to CSV
- [ ] Scan multiple source accounts at once
- [ ] Filter by location or bio keywords
- [ ] Support for organizations

---

*Built by [Panshul Vempalli](https://github.com/PanshulVempalli) · Base concept by [Urvish L.](https://github.com/urvish)*
