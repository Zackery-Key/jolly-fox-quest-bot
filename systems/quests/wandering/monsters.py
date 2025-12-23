from typing import TypedDict, List


class WanderingMonster(TypedDict):
    title: str
    description: str
    difficulty: str


WANDERING_MONSTERS: List[WanderingMonster] = [

# ────────────────
# MINOR THREATS
# ────────────────
{
    "title": "Mist-Touched Strays",
    "description": "Feral animals warped by lingering arcane fog snap at anything that moves.",
    "difficulty": "minor",
},
{
    "title": "Candle-Watch Wisps",
    "description": "Small floating lights hover near roads, luring travelers off the path.",
    "difficulty": "minor",
},
{
    "title": "Grave-Dust Crawlers",
    "description": "Bone-white insects spill from disturbed burial sites, biting and burrowing.",
    "difficulty": "minor",
},
{
    "title": "Fogbound Pickpockets",
    "description": "Shadowy figures dart through the mist, vanishing with coin and keys.",
    "difficulty": "minor",
},
{
    "title": "Murmurleaf Thicket",
    "description": "Shrubs whisper and shift, entangling passersby who linger too long.",
    "difficulty": "minor",
},
{
    "title": "Cracked Lantern Spirits",
    "description": "Flickering spirits cling to old lamps, flaring violently when disturbed.",
    "difficulty": "minor",
},
{
    "title": "Ashfall Beetle Swarm",
    "description": "A chittering mass of ember-dusted beetles rolls across the ground.",
    "difficulty": "minor",
},
{
    "title": "Lost Pack Animals",
    "description": "Abandoned beasts wander in a panic, kicking and charging through camps.",
    "difficulty": "minor",
},
{
    "title": "Mist-Hollow Bats",
    "description": "Clouds of pale bats erupt from ruined structures at dusk.",
    "difficulty": "minor",
},
{
    "title": "Veil-Sick Travelers",
    "description": "Confused wanderers lash out, convinced the party are figments of the mist.",
    "difficulty": "minor",
},
{
    "title": "Grasping Fogbanks",
    "description": "Thick fog congeals into chilling tendrils that pull at boots and cloaks.",
    "difficulty": "minor",
},
{
    "title": "Echoing Footsteps",
    "description": "Invisible presences pace nearby, causing panic and false alarms.",
    "difficulty": "minor",
},


# ────────────────
# STANDARD THREATS
# ────────────────
{
    "title": "Mistbound Marauders",
    "description": "Bandits cloaked in enchanted fog ambush travelers along trade paths.",
    "difficulty": "standard",
},
{
    "title": "Gravecoil Serpent",
    "description": "A massive serpent nests among tombstones, striking from below.",
    "difficulty": "standard",
},
{
    "title": "Veil-Warped Brute",
    "description": "A lone humanoid twisted by magic rampages without reason or memory.",
    "difficulty": "standard",
},
{
    "title": "Hollow Watchtower Warden",
    "description": "An abandoned guard tower stirs, animated by lingering duty and rage.",
    "difficulty": "standard",
},
{
    "title": "Mist-Harvest Coven",
    "description": "Ritualists gather arcane fog in crystal vessels for unknown purposes.",
    "difficulty": "standard",
},
{
    "title": "Briarhide Charger",
    "description": "A horned beast armored in thorned bark storms through the vale.",
    "difficulty": "standard",
},
{
    "title": "Echo-Walkers",
    "description": "Phantom figures mimic the party’s movements, attacking at opportune moments.",
    "difficulty": "standard",
},
{
    "title": "Gravemark Reavers",
    "description": "Desecrators plunder burial grounds, guarded by crude undead constructs.",
    "difficulty": "standard",
},
{
    "title": "Fogshard Elemental",
    "description": "Condensed mist crystallizes into a hostile elemental form.",
    "difficulty": "standard",
},
{
    "title": "Moon-Scarred Hunter",
    "description": "A cursed tracker stalks prey under lunar influence, unable to stop.",
    "difficulty": "standard",
},


    # ────────────────
    # MAJOR THREATS
    # ────────────────
    {
        "title": "Rootbound Colossus",
        "description": "Ancient roots tear free from the earth, forming a towering guardian.",
        "difficulty": "major",
    },
    {
        "title": "Mistbound Behemoth",
        "description": "A massive silhouette moves within the fog, its footsteps shaking the vale.",
        "difficulty": "major",
    },
    {
        "title": "Gravetide Herald",
        "description": "A robed figure rings a rusted bell, raising the dead with each toll.",
        "difficulty": "major",
    },
    {
        "title": "The Hollow Huntsman",
        "description": "A headless rider emerges from the mist, tracking those marked by fate.",
        "difficulty": "major",
    },
    {
        "title": "Veins of the Vale",
        "description": "The land itself ruptures, spawning living stone and wrathful earth-spirits.",
        "difficulty": "major",
    },

    # ────────────────
    # CRITICAL THREATS
    # ────────────────
    {
        "title": "Veilbreak Manifestation",
        "description": "Reality thins as something pushes through from beyond the veil.",
        "difficulty": "critical",
    },
    {
        "title": "The Mist Sovereign",
        "description": "A towering entity of fog and will claims dominion over the vale itself.",
        "difficulty": "critical",
    },
    {
        "title": "Cataclysm Bloom",
        "description": "A massive arcane growth pulses violently, warping everything nearby.",
        "difficulty": "critical",
    },
    {
        "title": "Echo of a Slumbering Titan",
        "description": "A fragment of a greater being awakens, reshaping the land with each movement.",
        "difficulty": "critical",
    },
    {
        "title": "The Veiled Catastrophe",
        "description": "An approaching calamity made manifest, heralding devastation if unchecked.",
        "difficulty": "critical",
    },
]

