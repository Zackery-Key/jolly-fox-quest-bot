import random
from datetime import date

from . import storage
from .quest_models import QuestTemplate, QuestType


class QuestManager:
    def __init__(self):
        self.quest_templates = storage.load_templates()
        self.npcs = storage.load_npcs()
        self.players = storage.load_players()
        self.quest_board = storage.load_board()

        print(f"Loaded {len(self.quest_templates)} quest templates.")
        print(f"Loaded {len(self.npcs)} NPCs.")
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
    def get_player(self, user_id):
        return self.players.get(user_id)

    def get_or_create_player(self, user_id):
        if user_id not in self.players:
            self.players[user_id] = PlayerState(user_id=user_id)
            storage.save_players(self.players)
        return self.players[user_id]

    # -----------------------------------------------------
    # Daily Quest Assignment
    # -----------------------------------------------------
    def assign_daily(self, user_id):
        player = self.get_or_create_player(user_id)
        today = str(date.today())

        if player.daily_quest.get("assigned_date") == today:
            return player.daily_quest["quest_id"]

        # Pick random quest ID
        quest_id = random.choice(list(self.quest_templates.keys()))
        player.daily_quest = {
            "quest_id": quest_id,
            "assigned_date": today,
            "completed": False
        }

        storage.save_players(self.players)
        return quest_id

    # -----------------------------------------------------
    # Completion
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

    # -----------------------------------------------------
    # Scoreboard
    # -----------------------------------------------------
    def get_scoreboard(self):
        total_lifetime = sum(p.lifetime_completed for p in self.players.values())
        total_season = sum(p.season_completed for p in self.players.values())
        return {
            "global_points": self.quest_board.global_points,
            "lifetime_completed": total_lifetime,
            "season_completed": total_season
        }
