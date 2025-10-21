"""
Merge all series summaries into weekly and season totals.

Usage:
    python -m utils.merge_stats

By default scans: data/series/*/series_summary.json
Writes:
    data/weekly_reports/week_<YYYY-Www>_report.json
    data/weekly_reports/week_<YYYY-Www>_report.txt
    data/season_totals.json
    data/season_totals.txt

Also updates the registry (players.json / teams.json) so lifetime
stats match the computed season totals (authoritative).
"""

from __future__ import annotations
import os
import json
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any, Tuple

from utils.registry import update_registry_from_totals, PLAYERS_FILE, TEAMS_FILE

SERIES_ROOT = os.path.join("data", "series")
WEEKLY_ROOT = os.path.join("data", "weekly_reports")
SEASON_TOTALS_JSON = os.path.join("data", "season_totals.json")
SEASON_TOTALS_TXT = os.path.join("data", "season_totals.txt")

# Keep these in sync with your models + reports
PLAYER_STAT_KEYS = [
    "points", "throws", "table_hits", "catches", "missed_catches",
    "sinks", "rim_hits", "rounds_won", "series_won"
]
TEAM_STAT_KEYS = [
    "total_points", "total_throws", "total_table_hits", "total_catches",
    "total_missed_catches", "total_sinks", "total_rim_hits",
    "total_rounds_won", "total_series_won"
]


def _safe_read_json(path: str) -> Dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _iso_week_key(date_str: str) -> str:
    """Return ISO week key 'YYYY-Www' for an ISO date 'YYYY-MM-DD'."""
    dt = datetime.fromisoformat(date_str)
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def _add_stats(dst: Dict[str, int], src: Dict[str, int], keys: list[str]):
    for k in keys:
        dst[k] = dst.get(k, 0) + int(src.get(k, 0))


def _scan_series_summaries(root: str) -> list[Dict[str, Any]]:
    out = []
    if not os.path.isdir(root):
        return out
    for name in os.listdir(root):
        series_dir = os.path.join(root, name)
        if not os.path.isdir(series_dir):
            continue
        summary_path = os.path.join(series_dir, "series_summary.json")
        if not os.path.exists(summary_path):
            continue
        data = _safe_read_json(summary_path)
        if data:
            out.append(data)
    return out


def merge_all(series_root: str = SERIES_ROOT) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Returns:
        weekly_reports: dict keyed by 'YYYY-Www' with per-player and per-team totals
        season_totals : dict with per-player and per-team totals across all weeks
    """
    weekly_reports: Dict[str, Any] = {}
    # season totals
    season_players: Dict[str, Dict[str, int]] = defaultdict(lambda: {k: 0 for k in PLAYER_STAT_KEYS})
    season_teams: Dict[str, Dict[str, int]] = defaultdict(lambda: {k: 0 for k in TEAM_STAT_KEYS})

    summaries = _scan_series_summaries(series_root)

    # Build weekly buckets
    weekly_players: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {k: 0 for k in PLAYER_STAT_KEYS})
    )
    weekly_teams: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {k: 0 for k in TEAM_STAT_KEYS})
    )

    for series in summaries:
        date = series.get("date")
        if not date:
            # skip if no date
            continue
        wk = _iso_week_key(date)

        # Players
        players_block = series.get("players", {})
        for pname, pstats in players_block.items():
            _add_stats(weekly_players[wk][pname], pstats, PLAYER_STAT_KEYS)
            _add_stats(season_players[pname], pstats, PLAYER_STAT_KEYS)

        # Teams
        teams_block = series.get("teams", {})
        for tname, tstats in teams_block.items():
            _add_stats(weekly_teams[wk][tname], tstats, TEAM_STAT_KEYS)
            _add_stats(season_teams[tname], tstats, TEAM_STAT_KEYS)

    # finalize weekly dicts
    for wk in sorted(weekly_players.keys()):
        weekly_reports[wk] = {
            "players": dict(weekly_players[wk]),
            "teams": dict(weekly_teams[wk])
        }

    season_totals = {
        "players": dict(season_players),
        "teams": dict(season_teams)
    }

    return weekly_reports, season_totals


def _ensure_dirs():
    os.makedirs(WEEKLY_ROOT, exist_ok=True)
    os.makedirs(os.path.dirname(SEASON_TOTALS_JSON), exist_ok=True)


def write_outputs(weekly_reports: Dict[str, Any], season_totals: Dict[str, Any]):
    from utils.report_generator import (
        render_weekly_text, render_season_text
    )

    _ensure_dirs()

    # Weekly JSON + TXT
    for week_key, data in weekly_reports.items():
        week_json_path = os.path.join(WEEKLY_ROOT, f"week_{week_key}_report.json")
        week_txt_path = os.path.join(WEEKLY_ROOT, f"week_{week_key}_report.txt")
        with open(week_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        with open(week_txt_path, "w", encoding="utf-8") as f:
            f.write(render_weekly_text(week_key, data))

    # Season JSON + TXT
    with open(SEASON_TOTALS_JSON, "w", encoding="utf-8") as f:
        json.dump(season_totals, f, indent=4)
    with open(SEASON_TOTALS_TXT, "w", encoding="utf-8") as f:
        f.write(render_season_text(season_totals))

    # NEW: Update registry so lifetime stats == computed season totals
    players_updated, teams_updated = update_registry_from_totals(
        players_totals=season_totals.get("players", {}),
        teams_totals=season_totals.get("teams", {}),
        overwrite=True  # authoritative sync
    )

    print(f"✅ Registry sync complete: players updated={players_updated}, teams updated={teams_updated}")
    print(f"   Players file: {PLAYERS_FILE}")
    print(f"   Teams file:   {TEAMS_FILE}")


def main():
    weekly_reports, season_totals = merge_all(SERIES_ROOT)
    write_outputs(weekly_reports, season_totals)
    print(f"✅ Merge complete. Weekly reports in '{WEEKLY_ROOT}', season totals in '{SEASON_TOTALS_JSON}' / '{SEASON_TOTALS_TXT}'.")


if __name__ == "__main__":
    main()
