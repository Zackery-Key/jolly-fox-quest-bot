import random
from datetime import date

from . import storage
from .quest_models import QuestTemplate, QuestType
from .player_state import PlayerState


class QuestManager:
    def __init__(self):
        # Load all dynamic data via storage layer
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

    def reload_templates(self):
        """Reload quest templates after import."""
        self.quest_templates = storage.load_templates()
        print(f"Reloaded {len(self.quest_templates)} quest templates.")


    # -----------------------------------------------------
    # Player access / management
    # -----------------------------------------------------
    def get_player(self, user_id):
        return self.players.get(user_id)

    def get_or_create_player(self, user_id):
        if user_id not in self.players:
            self.players[user_id] = PlayerState(user_id=user_id)
            storage.save_players(self.players)
        return self.players[user_id]

    def save_players(self):
        """Persist all current players."""
        storage.save_players(self.players)

    def clear_player(self, user_id):
        """Remove a player's data entirely."""
        if user_id in self.players:
            del self.players[user_id]
            storage.save_players(self.players)
            return True
        return False
    

    def _template_allowed_for_roles(self, template: QuestTemplate, role_ids: list[int]) -> bool:
        """
        Return True if the given quest template can be assigned
        to a user with the specified role IDs.

        Rules:
        - If template.allowed_roles is empty → everyone can get it.
        - Otherwise, user must have at least ONE of the allowed role IDs.
        """
        if not template.allowed_roles:
            return True

        role_set = set(role_ids)
        return any(role_id in role_set for role_id in template.allowed_roles)
    
    # -----------------------------------------------------
    # Daily Quest Assignment
    # -----------------------------------------------------
    def assign_daily(self, user_id: int, role_ids: list[int]) -> str | None:
        """
        Assign a daily quest to the user if they don't already have one today
        AND there is at least one quest they are allowed to receive based on roles.

        Returns:
            quest_id (str) if a quest is assigned or already exists for today,
            None if there are currently no eligible quests for the user's roles.
        """
        player = self.get_or_create_player(user_id)
        today = str(date.today())

        # If a quest is already assigned for today, keep it.
        if player.daily_quest.get("assigned_date") == today:
            return player.daily_quest.get("quest_id")

        # Defensive: no templates loaded
        if not self.quest_templates:
            raise RuntimeError("No quest templates loaded; cannot assign daily quest.")

        # Filter templates by allowed_roles vs user roles
        eligible_templates: list[QuestTemplate] = []
        for t in self.quest_templates.values():
            print("DEBUG Template:", t.quest_id, "Allowed:", t.allowed_roles)
            if self._template_allowed_for_roles(t, role_ids):
                eligible_templates.append(t)

        # If no eligible quests → no quest today (Option B).
        # User may try again later in the same day AFTER getting new roles.
        if not eligible_templates:
            # Clear any old daily_quest data for safety
            player.daily_quest = {}
            storage.save_players(self.players)
            return None

        # Pick random quest from eligible list
        chosen = random.choice(eligible_templates)
        quest_id = chosen.quest_id

        # Store the new daily quest with a role snapshot
        player.daily_quest = {
            "quest_id": quest_id,
            "assigned_date": today,
            "completed": False,
            # Snapshot of roles at assignment time
            "role_snapshot": list(role_ids),
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

    def save_board(self):
        storage.save_board(self.quest_board)

    def award_points(self, user_id: int, amount: int, faction_id: str | None = None):
        """
        Award guild points for a quest completion.
        Always increases global points.
        Also increases faction points if faction_id is provided.
        """
        if amount <= 0:
            return

        # Global seasonal points
        self.quest_board.global_points += amount

        # Faction bucket
        if faction_id:
            current = self.quest_board.faction_points.get(faction_id, 0)
            self.quest_board.faction_points[faction_id] = current + amount

        # Persist
        self.save_board()

    
    def get_scoreboard(self):
        total_lifetime = sum(p.lifetime_completed for p in self.players.values())
        total_season = sum(p.season_completed for p in self.players.values())
        return {
            "global_points": self.quest_board.global_points,
            "lifetime_completed": total_lifetime,
            "season_completed": total_season
        }
