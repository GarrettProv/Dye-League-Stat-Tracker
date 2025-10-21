from dataclasses import dataclass, field
from typing import Optional
from .team import Team

@dataclass
class Game:
    game_id: str
    series_id: str
    game_number: int
    team1: Team
    team2: Team
    winner: Optional[str] = None

    def end_game(self, winner_name: str):
        """Called when a game ends."""
        self.winner = winner_name

    def to_dict(self):
        return {
            "game_id": self.game_id,
            "series_id": self.series_id,
            "game_number": self.game_number,
            "team1": self.team1.to_dict(),
            "team2": self.team2.to_dict(),
            "winner": self.winner
        }
