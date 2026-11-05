# Job Watcher

Checks LinkedIn's public job search every ~15 minutes (GitHub Actions) and sends new matching jobs to Telegram.

- `config.json` — keywords, locations, experience levels, title include/exclude rules.
- `watch.py` — the checker (Python standard library only). `python watch.py --dry-run` prints matches locally.
- `seen.json` — jobs already sent (auto-updated by the workflow, pruned after `keep_seen_days`).
- Secrets (repo → Settings → Secrets and variables → Actions): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

Experience levels (`f_E`): 1 Internship, 2 Entry level, 3 Associate, 4 Mid-Senior, 5 Director.
LinkedIn geoIds: Egypt `106155005`, Worldwide `92000000`.
