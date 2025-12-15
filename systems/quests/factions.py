from dataclasses import dataclass
from typing import Dict, Optional
import discord

FACTION_ROLE_IDS = {
    "shieldborne": 1447646082459762761,
    "spellfire":   1447646480889548800,
    "verdant":     1447644562397859921,
}


@dataclass
class Faction:
    faction_id: str
    name: str
    emoji: str
    description: str


FACTIONS: Dict[str, Faction] = {
    "shieldborne": Faction(
        faction_id="shieldborne",
        name="Shieldborne Order",
        emoji="🛡️",
        description="Stalwart defenders who shield the guild and its allies.",
    ),
    "spellfire": Faction(
        faction_id="spellfire",
        name="Spellfire Conclave",
        emoji="🔥",
        description="Mages and arcanists who wield raw power in the guild’s name.",
    ),
    "verdant": Faction(
        faction_id="verdant",
        name="Verdant Circle",
        emoji="🌿",
        description="Wardens of life and nature who keep the guild thriving.",
    ),
}


def get_faction(faction_id: str) -> Optional[Faction]:
    if not faction_id:
        return None
    return FACTIONS.get(faction_id.lower())


def get_member_faction_id(member: discord.Member) -> str | None:
    role_ids = {role.id for role in member.roles}
    for faction_id, rid in FACTION_ROLE_IDS.items():
        if rid in role_ids:
            return faction_id
    return None

