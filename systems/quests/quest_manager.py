import os
import json
from datetime import date

from .quest_models import QuestTemplate
from .npc_models import NPC
from .player_state import PlayerState
from .quest_board import QuestBoard


DATA_DIR = "data"
QUESTS_FILE = os.path.join(DATA_DIR, "quests.json")
NPCS_FILE = os.path.join(DATA_DIR, "npcs.json")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")
BOARD_FILE = os.path.join(DATA_DIR, "quest_board.json")


class QuestManager:
    def __init__(self):
        # Ensure data directory + files exist
        self._ensure_file(QUESTS_FILE, default=[])
        self._ensure_file(NPCS_FILE, default=[])
        self._ensure_file(PLAYERS_FILE, default={})
        self._ensure_file(BOARD_FILE, default={"global_points": 0})

        # Load everything
        self.quest_templates = self._load_quest_templates()
        self.npcs = self._load_npcs()
        self.players = self._load_players()
        self.quest_board = self._load_board()

    # -----------------------------------------------------
    # Ensure files exist
    # -----------------------------------------------------
    def _ensure_file(self, path, default):
        """Creates the file with default content if missing."""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(default, f, indent=4)

    # -----------------------------------------------------
    # Loaders
    # -----------------------------------------------------
    def _load_quest_templates(self):
        with open(QUESTS_FILE, "r") as f:
            raw = json.load(f)
        return {q["quest_id"]: QuestTemplate(**q) for q in raw}

    def _load_npcs(self):
        with open(NPCS_FILE, "r") as f:
            raw = json.load(f)
        return {n["npc_id"]: NPC(**n) for n in raw}

    def _load_players(self):
        with open(PLAYERS_FILE, "r") as f:
            raw = json.load(f)

        players = {}
        for user_id, pdata in raw.items():
            players[int(user_id)] = PlayerState.from_dict(pdata)

        return players

    def _load_board(self):
        with open(BOARD_FILE, "r") as f:
            raw = json.load(f)

        return QuestBoard(global_points=raw.get("global_points", 0))

    # -----------------------------------------------------
    # Saving
    # -----------------------------------------------------
    def save_players(self):
        out = {uid: p.to_dict() for uid, p in self.players.items()}
        with open(PLAYERS_FILE, "w") as f:
            json.dump(out, f, indent=4)

    def save_board(self):
        with open(BOARD_FILE, "w") as f:
            json.dump({"global_points": self.quest_board.global_points}, f, indent=4)

    # -----------------------------------------------------
    # Accessors
    # -----------------------------------------------------
    def get_template(self, quest_id):
        return self.quest_templates.get(quest_id)

    def get_npc(self, npc_id):
        return self.npcs.get(npc_id)

    def get_player(self, user_id: int):
        """Return player state or None if player does not exist."""
        return self.players.get(user_id)

    def get_or_create_player(self, user_id: int):
        """Only create a profile when actually needed."""
        if user_id not in self.players:
            self.players[user_id] = PlayerState(user_id=user_id)
            self.save_players()
        return self.players[user_id]


    # -----------------------------------------------------
    # Player management helpers
    # -----------------------------------------------------
    def clear_player(self, user_id: int) -> bool:
        """Remove a single player's stored state."""
        if user_id in self.players:
            del self.players[user_id]
            self.save_players()
            return True
        return False

    def clear_all_players(self) -> None:
        """Dangerous: wipe all player data."""
        self.players = {}
        self.save_players()

    # -----------------------------------------------------
    # Daily Quest Assignment
    # -----------------------------------------------------
    def assign_daily(self, user_id):
        """Assigns a daily quest if the user has none or it's a new day."""
        player = self.get_player(user_id)

        today = str(date.today())

        # If already has today's quest, do nothing
        if (player.daily_quest 
            and player.daily_quest.get("assigned_date") == today):
            return player.daily_quest["quest_id"]

        # Otherwise assign a random quest
        import random
        quest_id = random.choice(list(self.quest_templates.keys()))

        player.daily_quest = {
            "quest_id": quest_id,
            "assigned_date": today,
            "completed": False
        }

        self.save_players()
        return quest_id

    # -----------------------------------------------------
    # Completing quests
    # -----------------------------------------------------
    def complete_daily(self, user_id: int):
        """Marks daily quest as completed and awards XP & stats."""
        player = self.get_player(user_id)

        # Already completed? Don't double-award.
        if player.daily_quest.get("completed"):
            return

        # Mark quest complete
        player.daily_quest["completed"] = True

        # --- NEW: Stats tracking ---
        player.lifetime_completed += 1
        player.season_completed += 1

        # --- NEW: XP award ---
        # You can tweak this! For now every quest gives +5 XP.
        xp_gain = 5
        player.xp += xp_gain

        # Level-up logic
        while player.xp >= player.level * 20:
            player.xp -= player.level * 20
            player.level += 1

        # Save after changes
        self.save_players()

        return True
