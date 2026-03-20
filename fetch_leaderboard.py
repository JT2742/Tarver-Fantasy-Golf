import urllib.request
import json
import os
from datetime import datetime, timedelta

ESPN_SCOREBOARD = "http://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard"
ESPN_SCHEDULE   = "http://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard?limit=5&dates={}"

# Same course pars database as the app
COURSE_PARS = {
    'masters':           [4,5,4,3,4,3,4,5,4,4,4,3,5,4,5,3,4,4],
    'augusta':           [4,5,4,3,4,3,4,5,4,4,4,3,5,4,5,3,4,4],
    'pebble beach':      [4,5,4,4,3,5,3,4,4,4,4,3,4,5,4,4,3,5],
    'riviera':           [4,4,3,4,5,4,4,3,4,5,4,3,4,4,4,3,4,4],
    'bay hill':          [4,4,3,4,5,4,4,3,4,4,3,4,5,4,4,3,4,5],
    'sawgrass':          [4,5,3,4,4,4,4,3,5,4,3,4,4,5,3,5,4,4],
    'tpc sawgrass':      [4,5,3,4,4,4,4,3,5,4,3,4,4,5,3,5,4,4],
    'quail hollow':      [4,4,3,5,4,4,3,4,4,4,3,4,5,4,3,4,4,4],
    'muirfield village': [4,4,3,5,4,4,3,5,4,4,3,4,5,4,3,4,4,4],
    'valhalla':          [4,4,3,4,5,4,3,4,4,4,3,4,5,4,4,3,4,4],
    'pinehurst':         [4,4,3,5,4,4,4,3,4,4,4,3,4,5,4,3,4,4],
    'torrey pines':      [4,4,3,4,4,5,4,3,4,5,3,4,4,4,3,4,4,5],
    'east lake':         [4,4,3,4,5,4,3,4,4,4,3,4,4,5,3,4,4,4],
    'kapalua':           [4,5,3,4,4,4,4,3,4,4,3,4,4,5,4,3,4,4],
}

def get_pars_for(tournament_name):
    if not tournament_name:
        return None
    t = tournament_name.lower()
    best, best_len = None, 0
    for key, pars in COURSE_PARS.items():
        if key in t and len(key) > best_len:
            best, best_len = pars, len(key)
    return best

def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def parse_field(evt):
    field = []
    try:
        comps = evt.get("competitions", [])
        entries = comps[0].get("competitors", []) if comps else []
        for p in entries:
            name = (p.get("athlete") or {}).get("displayName", "")
            status = p.get("status", {})
            pos = (status.get("position") or {}).get("displayValue", str(p.get("sortOrder", "")))
            score_val = p.get("score", "E")
            thru = status.get("thru", "")
            try:
                score_num = 0 if score_val == "E" else int(score_val)
            except:
                score_num = 0
            if name:
                field.append({"name": name, "pos": str(pos), "score": score_num, "thru": str(thru)})
    except Exception as e:
        print(f"  Parse error: {e}")
    field.sort(key=lambda x: x["score"])
    return field

def main():
    output = {"event": "", "field": [], "next_event": "", "next_pars": None}

    # 1. Current tournament
    try:
        data = fetch_url(ESPN_SCOREBOARD)
        events = data.get("events", [])
        if events:
            evt = events[0]
            output["event"] = evt.get("name", "")
            output["field"] = parse_field(evt)
            print(f"Current: {output['event']} — {len(output['field'])} players")
    except Exception as e:
        print(f"Current event fetch failed: {e}")

    # 2. Next week's tournament (look ahead 7 days)
    try:
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y%m%d")
        data2 = fetch_url(ESPN_SCHEDULE.format(next_week))
        events2 = data2.get("events", [])
        if events2:
            next_evt = events2[0]
            next_name = next_evt.get("name", "")
            next_pars = get_pars_for(next_name)
            if next_name:
                output["next_event"] = next_name
                output["next_pars"] = next_pars
                print(f"Next week: {next_name}{' — pars found' if next_pars else ''}")
    except Exception as e:
        print(f"Next event fetch failed (non-critical): {e}")

    os.makedirs("public", exist_ok=True)
    with open("public/leaderboard.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved to public/leaderboard.json")

if __name__ == "__main__":
    main()
