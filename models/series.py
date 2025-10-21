from dataclasses import dataclass, field
from typing import List, Optional
from .game import Game
from .team import Team
from datetime import datetime
import os
from utils.storage import save_json, save_text

@dataclass
class Series:
    series_id: str
    date: str
    team1: Team
    team2: Team
    games: List[Game] = field(default_factory=list)
    best_of: int = 3
    current_game: int = 0
    team1_wins: int = 0
    team2_wins: int = 0
    winner: Optional[str] = None

    def start_new_game(self):
        self.current_game += 1
        self.team1.reset_game_stats()
        self.team2.reset_game_stats()
        gid = f"{self.series_id}_Game{self.current_game}"
        return Game(gid, self.series_id, self.current_game, self.team1, self.team2)

    def record_game(self, game: Game):
        """Adds finished game to the series."""
        self.games.append(game)
        if game.winner == self.team1.name:
            self.team1_wins += 1
        elif game.winner == self.team2.name:
            self.team2_wins += 1
        if self.current_game >= self.best_of:
            self.finish_series()

    def finish_series(self):
        self.winner = (
            self.team1.name
            if self.team1_wins > self.team2_wins
            else self.team2.name
        )
        self.save_summary()

    def save_summary(self):
        folder = os.path.join("data", "series", self.series_id)
        os.makedirs(folder, exist_ok=True)
        summary = {
            "series_id": self.series_id,
            "date": self.date,
            "team1": self.team1.name,
            "team2": self.team2.name,
            "games_played": self.current_game,
            "series_score": {self.team1.name: self.team1_wins, self.team2.name: self.team2_wins},
            "winner": self.winner,
            "players": {
                p.name: p.lifetime_stats for t in [self.team1, self.team2] for p in t.players
            },
            "teams": {
                self.team1.name: self.team1.lifetime_stats,
                self.team2.name: self.team2.lifetime_stats,
            },
        }
        save_json(os.path.join(folder, "series_summary.json"), summary)

        # human-readable version
        lines = [
            f"Series: {self.team1.name} vs {self.team2.name}",
            f"Date: {self.date}",
            f"Final Score: {self.team1.name} {self.team1_wins} - {self.team2_wins} {self.team2.name}",
            f"Winner: {self.winner}",
            "",
            "--- Player Totals ---",
        ]
        for p in [*self.team1.players, *self.team2.players]:
            stats = ", ".join([f"{k}: {v}" for k, v in p.lifetime_stats.items()])
            lines.append(f"{p.name} → {stats}")
        save_text(os.path.join(folder, "series_summary.txt"), "\n".join(lines))
