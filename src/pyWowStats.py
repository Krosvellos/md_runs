import csv
import random
import time
from pathlib import Path

import requests

MAX_PAGE = 1000
REQUEST_DELAY_SECONDS = 0.5
TIMEOUT_SECONDS = 20

BASE_URL_PREFIX = "https://raider.io/api/v1/mythic-plus/runs?access_key=RIO5dV3E78v36uBA7i1fbR85p&season=season-mn-1&region=eu&dungeon=Pit%20of%20Saron&page="
RUN_DETAILS_URL_PREFIX = "https://raider.io/api/v1/mythic-plus/run-details?access_key=RIO5dV3E78v36uBA7i1fbR85p&season=season-mn-1&id="

OUTPUT_PATH = Path.home() / "Desktop" / "raiderio_runs_saron_final.csv"


def safe_get(dct, *keys, default=None):
    current = dct
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def flatten_run(run_wrapper: dict, run_details: dict = None) -> dict:
    run = run_wrapper.get("run", {})

    roster = run_details.get("roster", []) if run_details else run.get("roster", [])

    tank = next((p for p in roster if p.get("role") == "tank"), {})
    healer = next((p for p in roster if p.get("role") == "healer"), {})
    dps_players = [p for p in roster if p.get("role") == "dps"]

    weekly_modifiers = run.get("weekly_modifiers", [])
    modifier_names = [m.get("name", "") for m in weekly_modifiers]

    keystone_time_ms = run.get("keystone_time_ms")

    return {
        # Identifiers
        "keystone_run_id": run.get("keystone_run_id"),
        "keystone_team_id": run.get("keystone_team_id"),
        "completed_at": run.get("completed_at"),  # for time-based splits, not a model feature
        # Pre-run features
        "season": run.get("season"),
        "mythic_level": run.get("mythic_level"),
        "keystone_time_ms": keystone_time_ms,
        "faction": run.get("faction"),
        "dungeon_name": safe_get(run, "dungeon", "name"),
        "dungeon_short_name": safe_get(run, "dungeon", "short_name"),
        "dungeon_slug": safe_get(run, "dungeon", "slug"),
        "dungeon_patch": safe_get(run, "dungeon", "patch"),
        "modifier_1": modifier_names[0] if len(modifier_names) > 0 else "",
        "modifier_2": modifier_names[1] if len(modifier_names) > 1 else "",
        "modifier_3": modifier_names[2] if len(modifier_names) > 2 else "",
        "tank_name": safe_get(tank, "character", "name"),
        "tank_race": safe_get(tank, "character", "race", "name"),
        "tank_race_id": safe_get(tank, "character", "race", "id"),
        "tank_class": safe_get(tank, "character", "class", "name"),
        "tank_class_id": safe_get(tank, "character", "class", "id"),
        "tank_spec": safe_get(tank, "character", "spec", "name"),
        "tank_spec_id": safe_get(tank, "character", "spec", "id"),
        "tank_ilvl": safe_get(tank, "items", "item_level_equipped"),
        "healer_name": safe_get(healer, "character", "name"),
        "healer_race": safe_get(healer, "character", "race", "name"),
        "healer_race_id": safe_get(healer, "character", "race", "id"),
        "healer_class": safe_get(healer, "character", "class", "name"),
        "healer_class_id": safe_get(healer, "character", "class", "id"),
        "healer_spec": safe_get(healer, "character", "spec", "name"),
        "healer_spec_id": safe_get(healer, "character", "spec", "id"),
        "healer_ilvl": safe_get(healer, "items", "item_level_equipped"),
        "dps_1_name": safe_get(dps_players[0], "character", "name") if len(dps_players) > 0 else "",
        "dps_1_race": safe_get(dps_players[0], "character", "race", "name") if len(dps_players) > 0 else "",
        "dps_1_race_id": safe_get(dps_players[0], "character", "race", "id") if len(dps_players) > 0 else "",
        "dps_1_class": safe_get(dps_players[0], "character", "class", "name") if len(dps_players) > 0 else "",
        "dps_1_class_id": safe_get(dps_players[0], "character", "class", "id") if len(dps_players) > 0 else "",
        "dps_1_spec": safe_get(dps_players[0], "character", "spec", "name") if len(dps_players) > 0 else "",
        "dps_1_spec_id": safe_get(dps_players[0], "character", "spec", "id") if len(dps_players) > 0 else "",
        "dps_1_ilvl": safe_get(dps_players[0], "items", "item_level_equipped") if len(dps_players) > 0 else "",
        "dps_2_name": safe_get(dps_players[1], "character", "name") if len(dps_players) > 1 else "",
        "dps_2_race": safe_get(dps_players[1], "character", "race", "name") if len(dps_players) > 1 else "",
        "dps_2_race_id": safe_get(dps_players[1], "character", "race", "id") if len(dps_players) > 1 else "",
        "dps_2_class": safe_get(dps_players[1], "character", "class", "name") if len(dps_players) > 1 else "",
        "dps_2_class_id": safe_get(dps_players[1], "character", "class", "id") if len(dps_players) > 1 else "",
        "dps_2_spec": safe_get(dps_players[1], "character", "spec", "name") if len(dps_players) > 1 else "",
        "dps_2_spec_id": safe_get(dps_players[1], "character", "spec", "id") if len(dps_players) > 1 else "",
        "dps_2_ilvl": safe_get(dps_players[1], "items", "item_level_equipped") if len(dps_players) > 1 else "",
        "dps_3_name": safe_get(dps_players[2], "character", "name") if len(dps_players) > 2 else "",
        "dps_3_race": safe_get(dps_players[2], "character", "race", "name") if len(dps_players) > 2 else "",
        "dps_3_race_id": safe_get(dps_players[2], "character", "race", "id") if len(dps_players) > 2 else "",
        "dps_3_class": safe_get(dps_players[2], "character", "class", "name") if len(dps_players) > 2 else "",
        "dps_3_class_id": safe_get(dps_players[2], "character", "class", "id") if len(dps_players) > 2 else "",
        "dps_3_spec": safe_get(dps_players[2], "character", "spec", "name") if len(dps_players) > 2 else "",
        "dps_3_spec_id": safe_get(dps_players[2], "character", "spec", "id") if len(dps_players) > 2 else "",
        "dps_3_ilvl": safe_get(dps_players[2], "items", "item_level_equipped") if len(dps_players) > 2 else "",
        # Target variable
        "clear_time_ms": run.get("clear_time_ms"),
    }


def fetch_page(session: requests.Session, page: int) -> list[dict]:
    url = f"{BASE_URL_PREFIX}{page}"
    response = session.get(url, timeout=TIMEOUT_SECONDS, headers={"accept": "application/json"})
    response.raise_for_status()

    payload = response.json()

    if isinstance(payload, dict):
        rankings = payload.get("rankings", [])
        if isinstance(rankings, list):
            return rankings

    return []


def fetch_run_details(session: requests.Session, run_id: int) -> dict:
    url = f"{RUN_DETAILS_URL_PREFIX}{run_id}"
    response = session.get(url, timeout=TIMEOUT_SECONDS, headers={"accept": "application/json"})
    response.raise_for_status()
    return response.json()


def main():
    session = requests.Session()
    all_rows = []

    for page in range(0, MAX_PAGE + 1):
        try:
            rankings = fetch_page(session, page)
        except requests.RequestException as e:
            print(f"[ERROR] Page {page} failed: {e}")
            continue

        if not rankings:
            print(f"[INFO] Page {page} returned no runs. Stopping.")
            break

        for run_wrapper in rankings:
            run_id = run_wrapper.get("run", {}).get("keystone_run_id")
            run_details = {}
            if run_id:
                try:
                    print(f"  [INFO] Fetching details for run {run_id}...")
                    run_details = fetch_run_details(session, run_id)
                    time.sleep(REQUEST_DELAY_SECONDS)
                except requests.RequestException as e:
                    print(f"  [ERROR] Failed to fetch details for run {run_id}: {e}")

            all_rows.append(flatten_run(run_wrapper, run_details))

        print(f"[OK] Page {page}: collected {len(rankings)} runs")
        time.sleep(REQUEST_DELAY_SECONDS)

    if not all_rows:
        print("[INFO] No rows collected. CSV will not be created.")
        return

    random.shuffle(all_rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"[DONE] Saved {len(all_rows)} rows to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()