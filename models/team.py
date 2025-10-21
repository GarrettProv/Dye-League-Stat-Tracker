from dataclasses import dataclass, field
from typing import List
from .player import Player

@dataclass
class Team:
    name: str
    players: List[Player]
    lifetime_stats: dict = field(default_factory=lambda: {
        "total_points": 0,
        "total_throws": 0,              # ✅ NEW STAT
        "total_table_hits": 0,
        "total_catches": 0,
        "total_missed_catches": 0,
        "total_sinks": 0,
        "total_rim_hits": 0,
        "total_rounds_won": 0,
        "total_series_won": 0
    })
    current_game_stats: dict = field(default_factory=dict)
    current_series_stats: dict = field(default_factory=dict)

    def reset_game_stats(self):
        self.current_game_stats = {k: 0 for k in self.lifetime_stats.keys()}
        for p in self.players:
            p.reset_game_stats()

    def reset_series_stats(self):
        self.current_series_stats = {k: 0 for k in self.lifetime_stats.keys()}

    def add_stat(self, stat: str, amount: int = 1):
        if stat not in self.current_game_stats:
            self.current_game_stats[stat] = 0
        self.current_game_stats[stat] += amount
        self.lifetime_stats[stat] += amount
        if stat not in self.current_series_stats:
            self.current_series_stats[stat] = 0
        self.current_series_stats[stat] += amount

    def to_dict(self):
        return {
            "name": self.name,
            "players": [p.to_dict() for p in self.players],
            "lifetime_stats": self.lifetime_stats,
            "current_game_stats": self.current_game_stats,
            "current_series_stats": self.current_series_stats
        }

    @staticmethod
    def from_dict(data: dict):
        players = [Player.from_dict(p) for p in data["players"]]
        t = Team(data["name"], players)
        t.lifetime_stats = data.get("lifetime_stats", {})
        t.current_game_stats = data.get("current_game_stats", {})
        t.current_series_stats = data.get("current_series_stats", {})
        return t
