from dataclasses import dataclass

@dataclass
class Faction:
    faction_id: str
    name: str
    emoji: str
    description: str

FACTIONS = {
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

def get_faction(faction_id: str):
    return FACTIONS.get(str(faction_id).lower())
