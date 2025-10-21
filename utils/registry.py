import os
import json
from typing import List, Tuple, Dict, Optional
from models.player import Player
from models.team import Team

REGISTRY_DIR = "data/registry"
PLAYERS_FILE = os.path.join(REGISTRY_DIR, "players.json")
TEAMS_FILE = os.path.join(REGISTRY_DIR, "teams.json")


# -----------------------------
# Internal helpers
# -----------------------------
def _ensure_registry_dirs():
    os.makedirs(REGISTRY_DIR, exist_ok=True)

def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(path: str, data: dict) -> None:
    _ensure_registry_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def _default_player_stats() -> Dict[str, int]:
    # Keep in sync with Player.lifetime_stats
    return {
        "points": 0,
        "throws": 0,             # includes throws
        "table_hits": 0,
        "catches": 0,
        "missed_catches": 0,
        "sinks": 0,
        "rim_hits": 0,
        "rounds_won": 0,
        "series_won": 0
    }

def _default_team_stats() -> Dict[str, int]:
    # Keep in sync with Team.lifetime_stats
    return {
        "total_points": 0,
        "total_throws": 0,       # includes total_throws
        "total_table_hits": 0,
        "total_catches": 0,
        "total_missed_catches": 0,
        "total_sinks": 0,
        "total_rim_hits": 0,
        "total_rounds_won": 0,
        "total_series_won": 0
    }


# -----------------------------
# Public API (existing)
# -----------------------------
def load_registry() -> Tuple[dict, dict]:
    players = _load_json(PLAYERS_FILE)
    teams = _load_json(TEAMS_FILE)
    return players, teams

def save_registry(players: dict, teams: dict) -> None:
    _save_json(PLAYERS_FILE, players)
    _save_json(TEAMS_FILE, teams)

def list_team_names() -> List[str]:
    _, teams = load_registry()
    return sorted(list(teams.keys()))

def get_team_by_name(name: str) -> Optional[Team]:
    players_reg, teams_reg = load_registry()
    if name not in teams_reg:
        return None

    team_data = teams_reg[name]
    player_objs = []
    for pname in team_data.get("players", []):
        pstats = players_reg.get(pname, {})
        player = Player(pname)
        if pstats:
            # Merge known lifetime stats into the Player
            for k, v in pstats.items():
                player.lifetime_stats[k] = v
        player_objs.append(player)

    team = Team(name, player_objs)
    team.lifetime_stats.update(team_data.get("lifetime_stats", {}))
    return team

def update_registry_with_series(series) -> None:
    """
    Incrementally updates registry with the *delta* from a finished series.
    (Kept for GUI workflow compatibility.)
    """
    players_reg, teams_reg = load_registry()

    # Update players (lifetime totals)
    for team in [series.team1, series.team2]:
        for player in team.players:
            if player.name not in players_reg:
                players_reg[player.name] = dict(player.lifetime_stats)
            else:
                for k, v in player.lifetime_stats.items():
                    players_reg[player.name][k] = players_reg[player.name].get(k, 0) + v

    # Update teams (lifetime totals + ensure player list)
    for team in [series.team1, series.team2]:
        if team.name not in teams_reg:
            teams_reg[team.name] = {
                "lifetime_stats": dict(team.lifetime_stats),
                "players": [p.name for p in team.players],
            }
        else:
            for k, v in team.lifetime_stats.items():
                teams_reg[team.name]["lifetime_stats"][k] = teams_reg[team.name]["lifetime_stats"].get(k, 0) + v
            teams_reg[team.name]["players"] = [p.name for p in team.players]

    save_registry(players_reg, teams_reg)

def upsert_team(team_name: str, player_names: List[str]) -> None:
    """Create/update a team with given name and EXACTLY two players."""
    if len(player_names) != 2:
        raise ValueError("Teams must have exactly 2 players for 2v2.")

    players_reg, teams_reg = load_registry()

    # Ensure players exist in registry with at least empty stats
    for pname in player_names:
        if pname not in players_reg:
            players_reg[pname] = _default_player_stats()

    # Create/Update team entry
    if team_name not in teams_reg:
        teams_reg[team_name] = {
            "lifetime_stats": _default_team_stats(),
            "players": list(player_names)
        }
    else:
        teams_reg[team_name]["players"] = list(player_names)

    save_registry(players_reg, teams_reg)

def delete_team(team_name: str) -> bool:
    """Delete a team from registry. Players are NOT deleted."""
    players_reg, teams_reg = load_registry()
    if team_name in teams_reg:
        del teams_reg[team_name]
        save_registry(players_reg, teams_reg)
        return True
    return False


# -----------------------------
# NEW: Make registry match season totals computed by merge
# -----------------------------
def update_registry_from_totals(
    players_totals: Dict[str, Dict[str, int]],
    teams_totals: Dict[str, Dict[str, int]],
    overwrite: bool = True
) -> tuple[int, int]:
    """
    Update the registry so that lifetime stats equal the season totals
    computed by the merge (players_totals / teams_totals).

    - If a player/team does not exist, it will be created.
    - If overwrite=True (default): set stats to EXACT totals (authoritative).
      This avoids double counting / drift and makes all refs consistent.
    - If overwrite=False: will add totals on top of existing values (not recommended).

    Returns:
        (num_players_updated, num_teams_updated)

    NOTE: This function does *not* modify team player lists, since rosters
    cannot be reliably reconstructed from totals alone.
    """
    _ensure_registry_dirs()
    players_reg, teams_reg = load_registry()

    players_updated = 0
    teams_updated = 0

    # Players
    for pname, totals in players_totals.items():
        if pname not in players_reg:
            players_reg[pname] = _default_player_stats()
        if overwrite:
            new_stats = _default_player_stats()
            for k, v in totals.items():
                new_stats[k] = int(v)
            players_reg[pname] = new_stats
        else:
            for k, v in totals.items():
                players_reg[pname][k] = players_reg[pname].get(k, 0) + int(v)
        players_updated += 1

    # Teams
    for tname, totals in teams_totals.items():
        if tname not in teams_reg:
            teams_reg[tname] = {
                "lifetime_stats": _default_team_stats(),
                "players": teams_reg.get(tname, {}).get("players", [])
            }
        if overwrite:
            new_stats = _default_team_stats()
            for k, v in totals.items():
                new_stats[k] = int(v)
            teams_reg[tname]["lifetime_stats"] = new_stats
        else:
            for k, v in totals.items():
                teams_reg[tname]["lifetime_stats"][k] = teams_reg[tname]["lifetime_stats"].get(k, 0) + int(v)
        teams_updated += 1

    save_registry(players_reg, teams_reg)
    return players_updated, teams_updated
