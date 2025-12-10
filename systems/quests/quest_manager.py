import random
from datetime import date

from . import storage
from .quest_models import QuestTemplate, QuestType
from .npc_models import NPC
from .player_state import PlayerState
from .quest_board import QuestBoard


class QuestManager:
    def __init__(self):
        # Load all dynamic data via storage layer
        self.quest_templates = storage.load_templates()
        self.npcs = storage.load_npcs()
        self.players = storage.load_players()
        self.quest_board = storage.load_board()

        print("QuestManager Initialized")

    # -----------------------------------------------------
    # Template + NPC access
    # -----------------------------------------------------
    def get_template(self, quest_id):
        return self.quest_templates.get(quest_id)

    def get_npc(self, npc_id):
        return self.npcs.get(npc_id)

    # -----------------------------------------------------
    # Player access
    # -----------------------------------------------------
    def get_player(self, user_id: int):
        return self.players.get(user_id)

    def get_or_create_player(self, user_id: int):
        if user_id not in self.players:
            self.players[user_id] = PlayerState(user_id=user_id)
            storage.save_players(self.players)
        return self.players[user_id]

    # -----------------------------------------------------
    # Player cleaning
    # -----------------------------------------------------
    def clear_player(self, user_id: int) -> bool:
        if user_id in self.players:
            del self.players[user_id]
            storage.save_players(self.players)
            return True
        return False

    def clear_all_players(self):
        self.players = {}
        storage.save_players(self.players)

    # -----------------------------------------------------
    # Quest Board persistence
    # -----------------------------------------------------
    def save_board(self):
        storage.save_board(self.quest_board)

    # -----------------------------------------------------
    # Daily Quest Assignment
    # -----------------------------------------------------
    def assign_daily(self, user_id):
        player = self.get_or_create_player(user_id)
        today = str(date.today())

        if player.daily_quest.get("assigned_date") == today:
            return player.daily_quest["quest_id"]

        quest_id = random.choice(list(self.quest_templates.keys()))
        player.daily_quest = {
            "quest_id": quest_id,
            "assigned_date": today,
            "completed": False
        }

        storage.save_players(self.players)
        return quest_id

    # -----------------------------------------------------
    # Quest Completion
    # -----------------------------------------------------
    def complete_daily(self, user_id):
        player = self.get_or_create_player(user_id)

        if player.daily_quest.get("completed"):
            return False

        player.daily_quest["completed"] = True

        # Stats
        player.lifetime_completed += 1
        player.season_completed += 1

        # XP
        xp_gain = 5
        player.xp += xp_gain

        # Leveling
        while player.xp >= player.level * 20:
            player.xp -= player.level * 20
            player.level += 1

        storage.save_players(self.players)
        return True
