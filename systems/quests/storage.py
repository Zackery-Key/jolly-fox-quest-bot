import os
import json
from typing import Dict

from .player_state import PlayerState
from .quest_board import QuestBoard
from .npc_models import NPC
from .quest_models import QuestTemplate


# -------------------------------------------------
# Base paths (Persistent on Railway)
# -------------------------------------------------
DATA_DIR = "/mnt/data"
os.makedirs(DATA_DIR, exist_ok=True)

PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")
BOARD_FILE   = os.path.join(DATA_DIR, "quest_board.json")
NPCS_FILE    = os.path.join(DATA_DIR, "npcs.json")
QUESTS_FILE  = os.path.join(DATA_DIR, "quests.json")



# =================================================
# ===============  PLAYER STORAGE  ================
# =================================================

def load_players() -> Dict[int, PlayerState]:
    """Load PlayerState objects from JSON."""
    players: Dict[int, PlayerState] = {}

    if not os.path.exists(PLAYERS_FILE):
        return players

    with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    for key, pdata in raw.items():
        try:
            uid = int(key)
        except Exception:
            uid = pdata.get("user_id", 0)

        ps = PlayerState.from_dict(pdata)
        ps.user_id = uid
        players[uid] = ps

    return players


def save_players(players: Dict[int, PlayerState]) -> None:
    """Save all players to JSON."""
    raw = {str(uid): ps.to_dict() for uid, ps in players.items()}
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=4)


def save_player(player: PlayerState) -> None:
    """Update a single player entry."""
    players = load_players()
    players[player.user_id] = player
    save_players(players)


def delete_player(user_id: int) -> None:
    """Delete one player entry."""
    players = load_players()
    if user_id in players:
        del players[user_id]
    save_players(players)


# =================================================
# ===============   QUEST BOARD   =================
# =================================================

def load_board() -> QuestBoard:
    """Load global quest board (single document)."""
    board = QuestBoard()

    if not os.path.exists(BOARD_FILE):
        return board

    with open(BOARD_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    board.season_id = raw.get("season_id", "default_season")
    board.global_points = raw.get("global_points", 0)

    # Safe defaults if keys don't exist yet
    board.faction_points = raw.get("faction_points", {})
    board.display_channel_id = raw.get("display_channel_id")
    board.message_id = raw.get("message_id")
    board.season_goal = raw.get("season_goal", 100)
    board.faction_goal = raw.get("faction_goal", 250)
    board.season_reward = raw.get("season_reward", "")

    return board


def save_board(board: QuestBoard) -> None:
    """Persist global quest board."""
    data = {
        "season_id": board.season_id,
        "global_points": board.global_points,
        "faction_points": board.faction_points,
        "faction_goal": board.faction_goal,
        "display_channel_id": board.display_channel_id,
        "message_id": board.message_id,
        "season_goal": board.season_goal,
        "season_reward": board.season_reward,    
    }
    with open(BOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# =================================================
# ====================  NPCs  ======================
# =================================================

def load_npcs() -> Dict[str, NPC]:
    """Load NPCs from JSON."""
    npcs: Dict[str, NPC] = {}

    if not os.path.exists(NPCS_FILE):
        return npcs

    with open(NPCS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    for npc_id, npc_data in raw.items():
        npcs[npc_id] = NPC.from_dict(npc_data)

    return npcs


def save_npcs(npc_dict: Dict[str, object]) -> None:
    """Save NPCs to JSON. Supports NPC objects and raw dict structures."""
    raw = {}

    for npc_id, npc in npc_dict.items():
        # NPC object
        if hasattr(npc, "to_dict"):
            raw[npc_id] = npc.to_dict()

        # Raw dict (import)
        elif isinstance(npc, dict):
            raw[npc_id] = npc

        else:
            raise TypeError(f"NPC '{npc_id}' is not dict or NPC object")

    with open(NPCS_FILE, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=4)


def save_npc(npc: NPC) -> None:
    """Insert/update one NPC."""
    npcs = load_npcs()
    npcs[npc.npc_id] = npc
    save_npcs(npcs)


def delete_npc(npc_id: str) -> None:
    """Remove NPC by id."""
    npcs = load_npcs()
    if npc_id in npcs:
        del npcs[npc_id]
    save_npcs(npcs)


# =================================================
# ================ TEMPLATES ======================
# =================================================

def load_templates() -> Dict[str, QuestTemplate]:
    """Load quest templates from JSON."""
    templates: Dict[str, QuestTemplate] = {}

    if not os.path.exists(QUESTS_FILE):
        return templates

    with open(QUESTS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    for qid, qdata in raw.items():
        templates[qid] = QuestTemplate.from_dict(qdata)

    return templates


def save_templates(templates: Dict[str, QuestTemplate]) -> None:
    """Save all quest templates."""
    raw = {qid: t.to_dict() for qid, t in templates.items()}
    with open(QUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=4)


def save_template(template: QuestTemplate) -> None:
    """Insert or update a single quest template."""
    templates = load_templates()
    templates[template.quest_id] = template
    save_templates(templates)


def delete_template(quest_id: str) -> None:
    """Remove a quest template."""
    templates = load_templates()
    if quest_id in templates:
        del templates[quest_id]
    save_templates(templates)
