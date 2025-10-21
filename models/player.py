from dataclasses import dataclass, field

@dataclass
class Player:
    name: str
    lifetime_stats: dict = field(default_factory=lambda: {
        "points": 0,
        "throws": 0,              # ✅ NEW STAT
        "table_hits": 0,
        "catches": 0,
        "missed_catches": 0,
        "sinks": 0,
        "rim_hits": 0,
        "rounds_won": 0,
        "series_won": 0
    })
    current_game_stats: dict = field(default_factory=dict)
    current_series_stats: dict = field(default_factory=dict)

    def reset_game_stats(self):
        self.current_game_stats = {k: 0 for k in self.lifetime_stats.keys()}

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
            "lifetime_stats": self.lifetime_stats,
            "current_game_stats": self.current_game_stats,
            "current_series_stats": self.current_series_stats
        }

    @staticmethod
    def from_dict(data: dict):
        p = Player(data["name"])
        p.lifetime_stats = data.get("lifetime_stats", {})
        p.current_game_stats = data.get("current_game_stats", {})
        p.current_series_stats = data.get("current_series_stats", {})
        return p
