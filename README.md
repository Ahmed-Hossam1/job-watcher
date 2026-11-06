# Job Watcher

Checks LinkedIn's public job search every ~15 minutes (GitHub Actions) and sends new matching jobs to Telegram.

- `config.json` — keywords, locations, experience levels, title include/exclude rules.
- `watch.py` — the checker (Python standard library only). `python watch.py --dry-run` prints matches locally.
- `seen.json` — jobs already sent (auto-updated by the workflow, pruned after `keep_seen_days`).
- Secrets (repo → Settings → Secrets and variables → Actions): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

Experience levels (`f_E`): 1 Internship, 2 Entry level, 3 Associate, 4 Mid-Senior, 5 Director.
LinkedIn geoIds: Egypt `106155005`, European Union `91000000`, Europe incl. UK `100506914`, Worldwide `92000000`.

## Reliable every-15-min runs (cron-job.org)
GitHub's own `schedule` is best-effort and can run only every few hours. To get real 15-min runs, an external
cron calls the GitHub API every 15 minutes:
- URL: `POST https://api.github.com/repos/Ahmed-Hossam1/job-watcher/dispatches`
- Headers: `Authorization: Bearer <fine-grained token>`, `Accept: application/vnd.github+json`
- Body: `{"event_type": "tick"}`
- Token: fine-grained, only this repo, permission **Contents: Read and write**.
`posted_within_seconds` is 24h, so jobs are not missed when runs are late; `seen.json` prevents duplicates.
