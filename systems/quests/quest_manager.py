import json
from pathlib import Path
from typing import Dict, Optional

from .quest_models import QuestTemplate, QuestType
from .npc_models import NPC
from .player_state import PlayerState, InventoryItem
from .quest_board import QuestBoard


class QuestManager:
    """
    Handles loading and saving all quest-related data:
    - Quest templates
    - NPCs
    - Players
    - Quest board

    This is the main backend system used by discord commands.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_path = Path(data_dir)
        self.data_path.mkdir(exist_ok=True)

        # File paths
        self.quest_templates_file = self.data_path / "quest_templates.json"
        self.npcs_file = self.data_path / "npcs.json"
        self.players_file = self.data_path / "players.json"
        self.quest_board_file = self.data_path / "quest_board.json"

        # Loaded objects
        self.quest_templates: Dict[str, QuestTemplate] = {}
        self.npcs: Dict[str, NPC] = {}
        self.players: Dict[str, PlayerState] = {}
        self.quest_board: QuestBoard = QuestBoard()

        # Load data into memory
        self._load_all()

    # ----------------------------------------------------
    # -------------------- LOADING ------------------------
    # ----------------------------------------------------

    def _load_all(self):
        self._load_quest_templates()
        self._load_npcs()
        self._load_players()
        self._load_quest_board()

    def _load_quest_templates(self):
        if not self.quest_templates_file.exists():
            return

        with open(self.quest_templates_file, "r", encoding="utf8") as f:
            raw = json.load(f)

        for qid, data in raw.items():
            self.quest_templates[qid] = QuestTemplate(
                quest_id=qid,
                name=data["name"],
                type=QuestType(data["type"]),
                points=data["points"],
                required_channel_id=data.get("required_channel_id"),
                source_channel_id=data.get("source_channel_id"),
                turnin_channel_id=data.get("turnin_channel_id"),
                dc=data.get("dc"),
                points_on_success=data.get("points_on_success"),
                points_on_fail=data.get("points_on_fail"),
                npc_id=data.get("npc_id"),
                item_name=data.get("item_name"),
                summary=data.get("summary", ""),
                details=data.get("details", ""),
                tags=data.get("tags", []),
            )

    def _load_npcs(self):
        if not self.npcs_file.exists():
            return

        with open(self.npcs_file, "r", encoding="utf8") as f:
            raw = json.load(f)

        for npc_id, data in raw.items():
            self.npcs[npc_id] = NPC(
                npc_id=npc_id,
                name=data["name"],
                avatar_url=data["avatar_url"],
                default_reply=data["default_reply"],
            )

    def _load_players(self):
        if not self.players_file.exists():
            return

        with open(self.players_file, "r", encoding="utf8") as f:
            raw = json.load(f)

        for uid, data in raw.items():
            p = PlayerState(user_id=uid)

            # Load daily quest
            p.daily_quest = data.get("daily_quest")

            # Load inventory
            for item_data in data.get("inventory", []):
                p.inventory.append(
                    InventoryItem(
                        quest_id=item_data["quest_id"],
                        item_name=item_data["item_name"],
                        collected=item_data.get("collected", True),
                    )
                )

            self.players[uid] = p

    def _load_quest_board(self):
        if not self.quest_board_file.exists():
            return

        with open(self.quest_board_file, "r", encoding="utf8") as f:
            raw = json.load(f)

        self.quest_board.season_id = raw.get("season_id", "default_season")
        self.quest_board.global_points = raw.get("global_points", 0)

    # ----------------------------------------------------
    # -------------------- SAVING -------------------------
    # ----------------------------------------------------

    def save_all(self):
        self.save_quest_templates()
        self.save_npcs()
        self.save_players()
        self.save_quest_board()

    def save_quest_templates(self):
        raw = {}
        for qid, q in self.quest_templates.items():
            raw[qid] = {
                "name": q.name,
                "type": q.type.value,
                "points": q.points,
                "required_channel_id": q.required_channel_id,
                "source_channel_id": q.source_channel_id,
                "turnin_channel_id": q.turnin_channel_id,
                "dc": q.dc,
                "points_on_success": q.points_on_success,
                "points_on_fail": q.points_on_fail,
                "npc_id": q.npc_id,
                "item_name": q.item_name,
                "summary": q.summary,
                "details": q.details,
                "tags": q.tags,
            }

        with open(self.quest_templates_file, "w", encoding="utf8") as f:
            json.dump(raw, f, indent=2)

    def save_npcs(self):
        raw = {
            npc_id: {
                "name": npc.name,
                "avatar_url": npc.avatar_url,
                "default_reply": npc.default_reply,
            }
            for npc_id, npc in self.npcs.items()
        }

        with open(self.npcs_file, "w", encoding="utf8") as f:
            json.dump(raw, f, indent=2)

    def save_players(self):
        raw = {}

        for uid, p in self.players.items():
            raw[uid] = {
                "daily_quest": p.daily_quest,
                "inventory": [
                    {
                        "quest_id": item.quest_id,
                        "item_name": item.item_name,
                        "collected": item.collected,
                    }
                    for item in p.inventory
                ],
            }

        with open(self.players_file, "w", encoding="utf8") as f:
            json.dump(raw, f, indent=2)

    def save_quest_board(self):
        raw = {
            "season_id": self.quest_board.season_id,
            "global_points": self.quest_board.global_points,
        }

        with open(self.quest_board_file, "w", encoding="utf8") as f:
            json.dump(raw, f, indent=2)

    # ----------------------------------------------------
    # -------------------- HELPERS ------------------------
    # ----------------------------------------------------

    def get_template(self, quest_id: str) -> Optional[QuestTemplate]:
        return self.quest_templates.get(quest_id)

    def add_template(self, template: QuestTemplate):
        self.quest_templates[template.quest_id] = template
        self.save_quest_templates()

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        return self.npcs.get(npc_id)

    def add_npc(self, npc: NPC):
        self.npcs[npc.npc_id] = npc
        self.save_npcs()

    def get_player(self, user_id: int) -> PlayerState:
        uid = str(user_id)

        if uid not in self.players:
            self.players[uid] = PlayerState(user_id)
            self.save_players()

        return self.players[uid]

    def assign_daily(self, user_id: int, quest_id: str):
        p = self.get_player(user_id)
        p.assign_daily_quest(quest_id)
        self.save_players()

    def complete_daily(self, user_id: int):
        p = self.get_player(user_id)
        p.complete_daily_quest()
        self.save_players()
