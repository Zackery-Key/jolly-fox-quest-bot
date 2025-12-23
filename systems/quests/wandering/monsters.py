from typing import TypedDict, List


class WanderingMonster(TypedDict):
    title: str
    description: str
    difficulty: str


WANDERING_MONSTERS: List[WanderingMonster] = [
    {
        "title": "Ashen Wisp Swarm",
        "description": "Burning motes drift through Luneth Vale, feeding on fear and memory.",
        "difficulty": "minor",
    },
    {
        "title": "Moonfang Stalker",
        "description": "A silver-eyed predator prowls the mist, stalking lone travelers.",
        "difficulty": "standard",
    },
    {
        "title": "Rootbound Colossus",
        "description": "Ancient roots tear free from the earth, forming a towering guardian.",
        "difficulty": "major",
    },
    {
        "title": "Veilbreak Manifestation",
        "description": "Reality thins as something pushes through from beyond the veil.",
        "difficulty": "critical",
    },
]
