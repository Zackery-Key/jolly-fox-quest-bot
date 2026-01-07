from typing import TypedDict, List


class WanderingMonster(TypedDict):
    title: str
    description: str
    difficulty: str
    image: str 


WANDERING_MONSTERS: List[WanderingMonster] = [

# ────────────────
# MINOR THREATS
# ────────────────
{
    "title": "Mist-Touched Strays",
    "description": "Feral animals warped by lingering arcane fog snap at anything that moves.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459199827073306887/content.png?ex=6962693d&is=696117bd&hm=3f2978a7956e07173fd8e95cec1d12c00ba1dd4850901cc15d56eb922b0532cb&=&format=webp&quality=lossless",
},
{
    "title": "Candle-Watch Wisps",
    "description": "Small floating lights hover near roads, luring travelers off the path.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459200342607532062/content.png?ex=696269b8&is=69611838&hm=44ed330a6614fbc3709a312d85c79f49d0282d7bfbe5513bb93eed0c37bdf619&=&format=webp&quality=lossless",
},
{
    "title": "Grave-Dust Crawlers",
    "description": "Bone-white insects spill from disturbed burial sites, biting and burrowing.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Fogbound Pickpockets",
    "description": "Shadowy figures dart through the mist, vanishing with coin and keys.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Murmurleaf Thicket",
    "description": "Shrubs whisper and shift, entangling passersby who linger too long.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Cracked Lantern Spirits",
    "description": "Flickering spirits cling to old lamps, flaring violently when disturbed.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Ashfall Beetle Swarm",
    "description": "A chittering mass of ember-dusted beetles rolls across the ground.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Lost Pack Animals",
    "description": "Abandoned beasts wander in a panic, kicking and charging through camps.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Mist-Hollow Bats",
    "description": "Clouds of pale bats erupt from ruined structures at dusk.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Veil-Sick Travelers",
    "description": "Confused wanderers lash out, convinced the party are figments of the mist.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Grasping Fogbanks",
    "description": "Thick fog congeals into chilling tendrils that pull at boots and cloaks.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Echoing Footsteps",
    "description": "Invisible presences pace nearby, causing panic and false alarms.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},


# ────────────────
# STANDARD THREATS
# ────────────────
{
    "title": "Mistbound Marauders",
    "description": "Bandits cloaked in enchanted fog ambush travelers along trade paths.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Gravecoil Serpent",
    "description": "A massive serpent nests among tombstones, striking from below.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Veil-Warped Brute",
    "description": "A lone humanoid twisted by magic rampages without reason or memory.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Hollow Watchtower Warden",
    "description": "An abandoned guard tower stirs, animated by lingering duty and rage.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Mist-Harvest Coven",
    "description": "Ritualists gather arcane fog in crystal vessels for unknown purposes.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Briarhide Charger",
    "description": "A horned beast armored in thorned bark storms through the vale.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Echo-Walkers",
    "description": "Phantom figures mimic the party’s movements, attacking at opportune moments.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Gravemark Reavers",
    "description": "Desecrators plunder burial grounds, guarded by crude undead constructs.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Fogshard Elemental",
    "description": "Condensed mist crystallizes into a hostile elemental form.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Moon-Scarred Hunter",
    "description": "A cursed tracker stalks prey under lunar influence, unable to stop.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
},


    # ────────────────
    # MAJOR THREATS
    # ────────────────
    {
        "title": "Rootbound Colossus",
        "description": "Ancient roots tear free from the earth, forming a towering guardian.",
        "difficulty": "major",
        "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "Mistbound Behemoth",
        "description": "A massive silhouette moves within the fog, its footsteps shaking the vale.",
        "difficulty": "major",
        "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "Gravetide Herald",
        "description": "A robed figure rings a rusted bell, raising the dead with each toll.",
        "difficulty": "major",
        "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "The Hollow Huntsman",
        "description": "A headless rider emerges from the mist, tracking those marked by fate.",
        "difficulty": "major",
        "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "Veins of the Vale",
        "description": "The land itself ruptures, spawning living stone and wrathful earth-spirits.",
        "difficulty": "major",
        "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
    },

    # ────────────────
    # CRITICAL THREATS
    # ────────────────
    {
        "title": "Veilbreak Manifestation",
        "description": "Reality thins as something pushes through from beyond the veil.",
        "difficulty": "critical",
        "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "The Mist Sovereign",
        "description": "A towering entity of fog and will claims dominion over the vale itself.",
        "difficulty": "critical",
        "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "Cataclysm Bloom",
        "description": "A massive arcane growth pulses violently, warping everything nearby.",
        "difficulty": "critical",
        "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "Echo of a Slumbering Titan",
        "description": "A fragment of a greater being awakens, reshaping the land with each movement.",
        "difficulty": "critical",
        "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "The Veiled Catastrophe",
        "description": "An approaching calamity made manifest, heralding devastation if unchecked.",
        "difficulty": "critical",
        "image": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=69621617&is=6960c497&hm=5082f37a7972d1400dc27630cb67426cde08b0399f0e35471e4b27558feb0bb3&=&format=webp&quality=lossless&width=839&height=839",
    },
]

