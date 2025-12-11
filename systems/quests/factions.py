from dataclasses import dataclass
from typing import Dict, Optional


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
