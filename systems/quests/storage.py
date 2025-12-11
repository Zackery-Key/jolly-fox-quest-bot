import os
import json
from typing import Dict, List, Optional

from .player_state import PlayerState
from .quest_board import QuestBoard
from .npc_models import NPC
from .quest_models import QuestTemplate


# -------------------------------------------------
# Base paths
# -------------------------------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")
BOARD_FILE   = os.path.join(DATA_DIR, "quest_board.json")
NPCS_FILE    = os.path.join(DATA_DIR, "npcs.json")
QUESTS_FILE  = os.path.join(DATA_DIR, "quest.json")


# =================================================
# ===============  PLAYER STORAGE  ================
# =================================================

def load_players() -> Dict[int, PlayerState]:
    """Load PlayerState objects from JSON."""
    players = {}
    if not os.path.exists(PLAYERS_FILE):
        return players

    with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    for key, pdata in raw.items():
        try:
            uid = int(key)
        except:
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


# Single-player helpers (Mongo-style API)
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

    return board


def save_board(board: QuestBoard) -> None:
    """Persist global quest board."""
    data = {
        "season_id": board.season_id,
        "global_points": board.global_points,
    }
    with open(BOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# =================================================
# ====================  NPCs  ======================
# =================================================

def load_npcs() -> Dict[str, NPC]:
    """Load NPCs from JSON."""
    npcs = {}

    if not os.path.exists(NPCS_FILE):
        return npcs

    with open(NPCS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    for npc_id, npc_data in raw.items():
        npcs[npc_id] = NPC.from_dict(npc_data)

    return npcs


def save_npcs(npc_dict: Dict[str, NPC]) -> None:
    """Save all NPCs to JSON."""
    raw = {npc_id: npc.to_dict() for npc_id, npc in npc_dict.items()}
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
    templates = {}

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
