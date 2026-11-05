"""Job Watcher: polls LinkedIn's public (guest) job search and sends new matches to Telegram.

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID. Without them it runs as a dry run and prints matches.
Usage: python watch.py [--dry-run]
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0 Safari/537.36")


def load(name, default):
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fetch(params):
    req = urllib.request.Request(SEARCH_URL + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def text(pattern, block):
    m = re.search(pattern, block, re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def parse(page):
    jobs = []
    for block in page.split("<li")[1:]:
        job_id = re.search(r"jobPosting:(\d+)", block)
        if not job_id:
            continue
        jobs.append({
            "id": job_id.group(1),
            "title": text(r'base-search-card__title">(.*?)</h3>', block),
            "company": text(r'base-search-card__subtitle">(.*?)</h4>', block),
            "location": text(r'job-search-card__location">(.*?)</span>', block),
            "posted": text(r'datetime="([^"]+)"', block),
            "url": f"https://www.linkedin.com/jobs/view/{job_id.group(1)}/",
        })
    return jobs


def send_telegram(token, chat_id, job, location_name):
    msg = (f"🆕 <b>{html.escape(job['title'])}</b>\n"
           f"🏢 {html.escape(job['company'])}\n"
           f"📍 {html.escape(job['location'])} · {location_name}\n"
           f"🗓 {job['posted']}\n"
           f"{job['url']}")
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg, "parse_mode": "HTML",
                                   "disable_web_page_preview": "true"}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=30)


def main():
    cfg = load("config.json", {})
    seen = load("seen.json", {})
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    dry = "--dry-run" in sys.argv or not (token and chat_id)
    must = re.compile(cfg["title_must_match"], re.I)
    exclude = re.compile(cfg["title_exclude"], re.I)

    found, errors = [], 0
    for loc in cfg["locations"]:
        for kw in cfg["keywords"]:
            params = {"keywords": kw, "geoId": loc["geoId"], "f_TPR": f"r{cfg['posted_within_seconds']}",
                      "f_E": ",".join(cfg["experience_levels"]), "sortBy": "DD", "start": 0}
            if cfg.get("remote_only"):
                params["f_WT"] = "2"
            try:
                jobs = parse(fetch(params))
            except Exception as e:  # rate limit / network: skip this search, try the rest
                errors += 1
                print(f"! {loc['name']} / {kw}: {e}")
                jobs = []
            for job in jobs:
                if job["id"] in seen or any(j["id"] == job["id"] for j, _ in found):
                    continue
                if must.search(job["title"]) and not exclude.search(job["title"]):
                    found.append((job, loc["name"]))
            time.sleep(2)

    now = datetime.now(timezone.utc)
    sent = 0
    for job, loc_name in found[:cfg["max_messages_per_run"]]:
        print(f"+ {job['title']} | {job['company']} | {job['location']} | {job['url']}")
        if not dry:
            try:
                send_telegram(token, chat_id, job, loc_name)
                sent += 1
            except Exception as e:
                print(f"! telegram: {e}")
                continue
        seen[job["id"]] = now.date().isoformat()

    cutoff = (now - timedelta(days=cfg["keep_seen_days"])).date().isoformat()
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    if not dry:
        with open(os.path.join(ROOT, "seen.json"), "w", encoding="utf-8") as f:
            json.dump(seen, f, indent=0, sort_keys=True)
    print(f"matches={len(found)} sent={sent} search_errors={errors} dry_run={dry}")


if __name__ == "__main__":
    main()
