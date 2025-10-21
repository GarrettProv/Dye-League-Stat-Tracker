"""
Pretty text renderers (and helpers) for weekly/season reports.
You can extend these to also write CSV if you want.

Used by utils/merge_stats.py
"""

from __future__ import annotations
from typing import Dict, Any

PLAYER_ORDER = [
    "points", "throws", "catches", "missed_catches", "sinks",
    "table_hits", "rim_hits", "rounds_won", "series_won"
]
TEAM_ORDER = [
    "total_points", "total_throws", "total_catches", "total_missed_catches",
    "total_sinks", "total_table_hits", "total_rim_hits", "total_rounds_won", "total_series_won"
]

def _fmt_player_line(name: str, stats: Dict[str, int]) -> str:
    parts = [f"{k}:{stats.get(k,0)}" for k in PLAYER_ORDER]
    return f"{name}: " + ", ".join(parts)

def _fmt_team_line(name: str, stats: Dict[str, int]) -> str:
    parts = [f"{k}:{stats.get(k,0)}" for k in TEAM_ORDER]
    return f"{name}: " + ", ".join(parts)

def render_weekly_text(week_key: str, data: Dict[str, Any]) -> str:
    """
    data = {
        "players": { name: {...}, ... },
        "teams": { name: {...}, ... }
    }
    """
    lines = []
    lines.append(f"Weekly Report: {week_key}")
    lines.append("=" * (len(lines[-1])))
    lines.append("")

    # Teams first (scoreboard vibe)
    lines.append("--- Team Totals ---")
    for tname in sorted(data.get("teams", {}).keys()):
        lines.append(_fmt_team_line(tname, data["teams"][tname]))
    lines.append("")

    lines.append("--- Player Totals ---")
    for pname in sorted(data.get("players", {}).keys()):
        lines.append(_fmt_player_line(pname, data["players"][pname]))
    lines.append("")

    # Quick leaders (points/sinks/catches)
    lines.append("--- Weekly Leaders ---")
    leaders = _leaders_block(data.get("players", {}))
    lines.extend(leaders)
    lines.append("")

    return "\n".join(lines)

def render_season_text(season: Dict[str, Any]) -> str:
    """
    season = {
        "players": { name: {...}, ... },
        "teams": { name: {...}, ... }
    }
    """
    lines = []
    lines.append("Season Totals")
    lines.append("=============")
    lines.append("")

    lines.append("--- Team Totals ---")
    for tname in sorted(season.get("teams", {}).keys()):
        lines.append(_fmt_team_line(tname, season["teams"][tname]))
    lines.append("")

    lines.append("--- Player Totals ---")
    for pname in sorted(season.get("players", {}).keys()):
        lines.append(_fmt_player_line(pname, season["players"][pname]))
    lines.append("")

    lines.append("--- Season Leaders ---")
    leaders = _leaders_block(season.get("players", {}))
    lines.extend(leaders)
    lines.append("")

    return "\n".join(lines)

def _leaders_block(players: Dict[str, Dict[str, int]]) -> list[str]:
    """Return a simple leaders section for points/sinks/catches."""
    def top_n(stat: str, n=5):
        arr = [(name, stats.get(stat, 0)) for name, stats in players.items()]
        arr.sort(key=lambda x: x[1], reverse=True)
        return arr[:n]

    lines = []
    for stat in ["points", "throws", "sinks", "catches"]:
        top = top_n(stat, n=5)
        if not top:
            continue
        lines.append(f"{stat.capitalize()} Leaders:")
        for name, val in top:
            lines.append(f"  - {name}: {val}")
    return lines
