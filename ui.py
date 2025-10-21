import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from datetime import datetime
import os

from models.player import Player
from models.team import Team
from models.series import Series
from utils.storage import save_json
from utils.registry import get_team_by_name, update_registry_with_series

# --- CONFIG ---
STAT_NAMES = [
    "points",
    "throws",           # ✅ NEW STAT BUTTON
    "table_hits",
    "catches",
    "missed_catches",
    "sinks",
    "rim_hits",
    "rounds_won",
]


class DyeTrackerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dye Tournament Tracker")
        self.series = None
        self.current_game = None
        self.team1 = None
        self.team2 = None

        # Frames
        self.start_frame = tk.Frame(root)
        self.game_frame = tk.Frame(root)

        self.start_frame.pack(fill="both", expand=True)
        self.create_start_screen()

    # ------------------------------------------------
    # START SCREEN
    # ------------------------------------------------
    def create_start_screen(self):
        tk.Label(self.start_frame, text="🎲 Start New Series", font=("Arial", 18, "bold")).pack(pady=10)

        # Team 1 inputs
        t1_box = tk.LabelFrame(self.start_frame, text="Team 1", padx=10, pady=8)
        t1_box.pack(fill="x", padx=10, pady=6)
        tk.Label(t1_box, text="Team Name:").grid(row=0, column=0, sticky="w")
        self.team1_name = tk.Entry(t1_box, width=30)
        self.team1_name.grid(row=0, column=1, sticky="w")

        tk.Label(t1_box, text="Player 1 Name:").grid(row=1, column=0, sticky="w")
        self.team1_p1 = tk.Entry(t1_box, width=30)
        self.team1_p1.grid(row=1, column=1, sticky="w")

        tk.Label(t1_box, text="Player 2 Name:").grid(row=2, column=0, sticky="w")
        self.team1_p2 = tk.Entry(t1_box, width=30)
        self.team1_p2.grid(row=2, column=1, sticky="w")

        # Team 2 inputs
        t2_box = tk.LabelFrame(self.start_frame, text="Team 2", padx=10, pady=8)
        t2_box.pack(fill="x", padx=10, pady=6)
        tk.Label(t2_box, text="Team Name:").grid(row=0, column=0, sticky="w")
        self.team2_name = tk.Entry(t2_box, width=30)
        self.team2_name.grid(row=0, column=1, sticky="w")

        tk.Label(t2_box, text="Player 1 Name:").grid(row=1, column=0, sticky="w")
        self.team2_p1 = tk.Entry(t2_box, width=30)
        self.team2_p1.grid(row=1, column=1, sticky="w")

        tk.Label(t2_box, text="Player 2 Name:").grid(row=2, column=0, sticky="w")
        self.team2_p2 = tk.Entry(t2_box, width=30)
        self.team2_p2.grid(row=2, column=1, sticky="w")

        # Start button
        tk.Button(self.start_frame, text="Start Series", command=self.start_series, bg="#2c7", fg="white").pack(pady=12)

        # Registry help text
        hint = (
            "Hint: If a team name matches a team in the registry, their existing players "
            "and lifetime stats will load automatically. Leave player fields blank to use "
            "the registry players as-is."
        )
        tk.Label(self.start_frame, text=hint, fg="#666", wraplength=520, justify="left").pack(padx=10, pady=(0,10))

    def start_series(self):
        t1_name = (self.team1_name.get() or "").strip()
        t2_name = (self.team2_name.get() or "").strip()
        if not t1_name or not t2_name:
            messagebox.showerror("Error", "Please enter both team names.")
            return
        if t1_name == t2_name:
            messagebox.showerror("Error", "Team names must be different.")
            return

        # Try to load existing teams from registry
        existing_t1 = get_team_by_name(t1_name)
        existing_t2 = get_team_by_name(t2_name)

        # Build Team 1
        if existing_t1:
            # If registry has players, use them unless user supplied overrides
            p1_name_override = (self.team1_p1.get() or "").strip()
            p2_name_override = (self.team1_p2.get() or "").strip()
            if p1_name_override or p2_name_override:
                # Override players (new roster), keep lifetime team stats
                players = []
                n1 = p1_name_override or (existing_t1.players[0].name if existing_t1.players else "Unknown")
                n2 = p2_name_override or (existing_t1.players[1].name if len(existing_t1.players) > 1 else "Unknown")
                players = [Player(n1), Player(n2)]
                self.team1 = Team(t1_name, players)
                # retain lifetime team stats
                self.team1.lifetime_stats.update(existing_t1.lifetime_stats)
            else:
                # Use registry team as-is
                self.team1 = existing_t1
            messagebox.showinfo("Team Loaded", f"Loaded existing team from registry: {t1_name}")
        else:
            # New team 1
            p1 = (self.team1_p1.get() or "Unknown").strip()
            p2 = (self.team1_p2.get() or "Unknown").strip()
            self.team1 = Team(t1_name, [Player(p1), Player(p2)])

        # Build Team 2
        if existing_t2:
            p1_name_override = (self.team2_p1.get() or "").strip()
            p2_name_override = (self.team2_p2.get() or "").strip()
            if p1_name_override or p2_name_override:
                n1 = p1_name_override or (existing_t2.players[0].name if existing_t2.players else "Unknown")
                n2 = p2_name_override or (existing_t2.players[1].name if len(existing_t2.players) > 1 else "Unknown")
                players = [Player(n1), Player(n2)]
                self.team2 = Team(t2_name, players)
                self.team2.lifetime_stats.update(existing_t2.lifetime_stats)
            else:
                self.team2 = existing_t2
            messagebox.showinfo("Team Loaded", f"Loaded existing team from registry: {t2_name}")
        else:
            p1 = (self.team2_p1.get() or "Unknown").strip()
            p2 = (self.team2_p2.get() or "Unknown").strip()
            self.team2 = Team(t2_name, [Player(p1), Player(p2)])

        # Series setup
        today = datetime.now().strftime("%Y-%m-%d")
        series_id = f"{today}_{t1_name}_vs_{t2_name}"
        self.series = Series(series_id, today, self.team1, self.team2)
        os.makedirs(os.path.join("data", "series", series_id), exist_ok=True)

        # Transition to game screen
        self.start_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        self.create_game_screen()

    # ------------------------------------------------
    # GAME SCREEN
    # ------------------------------------------------
    def create_game_screen(self):
        self.clear_frame(self.game_frame)
        self.current_game = self.series.start_new_game()

        tk.Label(
            self.game_frame,
            text=f"🎮 Game {self.series.current_game} of {self.series.best_of}",
            font=("Arial", 16, "bold")
        ).pack(pady=6)

        # Team sections
        self.stat_labels = {}
        self.create_team_section(self.series.team1)
        self.create_team_section(self.series.team2)

        # End Game button row
        row = tk.Frame(self.game_frame)
        row.pack(pady=10)
        tk.Button(row, text="End Game", bg="#c33", fg="white", command=self.end_game).pack(side="left", padx=5)

        # Small legend
        tk.Label(
            self.game_frame,
            text="Click a stat to increment it for that player. Team totals update automatically.",
            fg="#666"
        ).pack(pady=(2, 8))

    def create_team_section(self, team):
        frame = tk.LabelFrame(self.game_frame, text=team.name, padx=10, pady=10, font=("Arial", 12, "bold"))
        frame.pack(padx=10, pady=6, fill="x")

        for player in team.players:
            self.create_player_row(frame, team, player)

    def create_player_row(self, parent, team, player):
        row = tk.Frame(parent)
        row.pack(pady=5, fill="x")

        tk.Label(row, text=player.name, width=14, anchor="w", font=("Arial", 11, "bold")).pack(side="left")

        # Buttons for each stat
        for stat in STAT_NAMES:
            btn = tk.Button(row, text=stat, command=lambda s=stat, p=player, t=team: self.add_stat(p, t, s))
            btn.pack(side="left", padx=2)

        # Live stat label
        label = tk.Label(row, text=self.format_stats(player), anchor="w")
        label.pack(side="left", padx=10)
        self.stat_labels[player.name] = label

    def add_stat(self, player, team, stat):
        # Update player
        player.add_stat(stat)
        # Update team; prefer "total_" prefixed keys if defined
        team_key = f"total_{stat}" if f"total_{stat}" in team.lifetime_stats else stat
        team.add_stat(team_key)

        # Update display
        self.update_player_display(player)

    def update_player_display(self, player):
        if player.name in self.stat_labels:
            self.stat_labels[player.name].config(text=self.format_stats(player))

    def format_stats(self, player):
        # Show current game stats (fresh each game)
        if not player.current_game_stats:
            return "(no stats yet)"
        return " | ".join([f"{k}:{v}" for k, v in player.current_game_stats.items()])

    # ------------------------------------------------
    # END GAME & NEXT GAME
    # ------------------------------------------------
    def end_game(self):
        winner = simpledialog.askstring("Winner", "Enter winning team name:")
        if not winner:
            messagebox.showerror("Error", "Must enter a winner.")
            return

        # Record and save game
        self.current_game.end_game(winner)
        self.series.record_game(self.current_game)

        folder = os.path.join("data", "series", self.series.series_id)
        path = os.path.join(folder, f"game_{self.series.current_game}.json")
        save_json(path, self.current_game.to_dict())

        # Move to next or finish series
        if self.series.current_game < self.series.best_of:
            messagebox.showinfo("Next Game", "Game saved! Moving to next game.")
            self.create_game_screen()
        else:
            # Mark series_won for players on winning team (lifetime stat)
            if self.series.winner == self.series.team1.name:
                for p in self.series.team1.players:
                    p.lifetime_stats["series_won"] = p.lifetime_stats.get("series_won", 0) + 1
                # Team lifetime series_won
                self.series.team1.lifetime_stats["total_series_won"] = \
                    self.series.team1.lifetime_stats.get("total_series_won", 0) + 1
            elif self.series.winner == self.series.team2.name:
                for p in self.series.team2.players:
                    p.lifetime_stats["series_won"] = p.lifetime_stats.get("series_won", 0) + 1
                self.series.team2.lifetime_stats["total_series_won"] = \
                    self.series.team2.lifetime_stats.get("total_series_won", 0) + 1

            # Save series summary files (json + txt handled in Series.save_summary)
            self.series.save_summary()

            # Update global registry with lifetime totals so future refs continue from here
            update_registry_with_series(self.series)

            messagebox.showinfo("Series Complete", f"Series complete! Winner: {self.series.winner}")
            self.root.quit()

    # Utility
    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()


# ------------------------------------------------
# RUN APP
# ------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = DyeTrackerUI(root)
    root.mainloop()
