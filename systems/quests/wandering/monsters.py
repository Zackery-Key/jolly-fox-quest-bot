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
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459200857978703912/content.png?ex=69626a33&is=696118b3&hm=5003f9f5344ace215c1d6d8ea60a5a557b2a1288778870f79926e5ff8bf7d194&=&format=webp&quality=lossless",
},
{
    "title": "Fogbound Pickpockets",
    "description": "Shadowy figures dart through the mist, vanishing with coin and keys.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459201257045626880/content.png?ex=69626a92&is=69611912&hm=bf0525e4f6d14e899280822239a5fc55529b568540df1fd84f64b2e7449339ac&=&format=webp&quality=lossless",
},
{
    "title": "Murmurleaf Thicket",
    "description": "Shrubs whisper and shift, entangling passersby who linger too long.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459201730658177199/content.png?ex=69626b03&is=69611983&hm=bf5dd8f20e17e18b23c7645980063bcbe7f04f7707baea2f822caa62cb7d8e19&=&format=webp&quality=lossless&width=350&height=350",
},
{
    "title": "Cracked Lantern Spirits",
    "description": "Flickering spirits cling to old lamps, flaring violently when disturbed.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459202364249477307/content.png?ex=69626b9a&is=69611a1a&hm=e4bb15c7ca7c84e1982c0484878f24b69bcc134046fa86fe3cc3ab17f1137173&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Ashfall Beetle Swarm",
    "description": "A chittering mass of ember-dusted beetles rolls across the ground.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459202914622111815/content.png?ex=69626c1d&is=69611a9d&hm=3b1f78b0023d144b8d661072ee5dd4ff293d45ebf394cd17f5e673766392845b&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Lost Pack Animals",
    "description": "Abandoned beasts wander in a panic, kicking and charging through camps.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459203534020018199/content.png?ex=69626cb1&is=69611b31&hm=a6b4cfedcd6642959bfc804f37daf112d56bc5834c09a04dfb33bacb8b332bdc&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Mist-Hollow Bats",
    "description": "Clouds of pale bats erupt from ruined structures at dusk.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459204043112054990/content.png?ex=69626d2a&is=69611baa&hm=97d6199a7b9cca04c540686c4f40dae9434b7af5af36a381d44799a7320ed2f8&=&format=webp&quality=lossless",
},
{
    "title": "Veil-Sick Travelers",
    "description": "Confused wanderers lash out, convinced the party are figments of the mist.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459207715090862170/content.png?ex=69627096&is=69611f16&hm=332a1d9082906420a0c9f38c3b1a69c9305475f7bd490d50f20b209b8e0a4cfa&=&format=webp&quality=lossless",
},
{
    "title": "Grasping Fogbanks",
    "description": "Thick fog congeals into chilling tendrils that pull at boots and cloaks.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459209286042390742/content.png?ex=6962720c&is=6961208c&hm=499b7048e54e3a543b33745b65843c764a7a23bfc6427828a2a06df4c2903618&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Echoing Footsteps",
    "description": "Invisible presences pace nearby, causing panic and false alarms.",
    "difficulty": "minor",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459210446996246619/content.png?ex=69627321&is=696121a1&hm=2217fde18b22efee87e92c1a34cb4e1b1b1ac1432c370999ebed506ee4c62f23&=&format=webp&quality=lossless",
},


# ────────────────
# STANDARD THREATS
# ────────────────
{
    "title": "Mistbound Marauders",
    "description": "Bandits cloaked in enchanted fog ambush travelers along trade paths.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459211240508227674/content.png?ex=696273de&is=6961225e&hm=be2af65e95c0ed027536287b55f1b5462e85ee2a3b410ad37a8f31fde0847c6a&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Gravecoil Serpent",
    "description": "A massive serpent nests among tombstones, striking from below.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459211727789887528/content.png?ex=69627452&is=696122d2&hm=a383dfad29d78b28b7821553962258f5e49cfa260a47052120c02d8cee912049&=&format=webp&quality=lossless",
},
{
    "title": "Veil-Warped Brute",
    "description": "A lone humanoid twisted by magic rampages without reason or memory.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459212179759960251/content.png?ex=696274be&is=6961233e&hm=06dad1181f2389de7dc4731d67861db4ebcc7c63ae4e633c5f697371099b3914&=&format=webp&quality=lossless&width=350&height=350",
},
{
    "title": "Hollow Watchtower Warden",
    "description": "An abandoned guard tower stirs, animated by lingering duty and rage.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459213382954778918/content.png?ex=696275dd&is=6961245d&hm=7001b49ececccb143329ccbb5ed2b99b8b6547a4d2aee1101409fa6d4de34085&=&format=webp&quality=lossless",
},
{
    "title": "Mist-Harvest Coven",
    "description": "Ritualists gather arcane fog in crystal vessels for unknown purposes.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459214435481550868/content.png?ex=696276d8&is=69612558&hm=f1c17c552afeb19b5944abcba3c0eb5be464e9938a3d5ddb410e4a6d398c49dc&=&format=webp&quality=lossless",
},
{
    "title": "Briarhide Charger",
    "description": "A horned beast armored in thorned bark storms through the vale.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459214875157856287/content.png?ex=69627741&is=696125c1&hm=2b0c225aa069893b1190f8da6937b0b3638075606a05e338f66ea72dc3ceb874&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Echo-Walkers",
    "description": "Phantom figures mimic the party’s movements, attacking at opportune moments.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459216814646231215/content.png?ex=6962790f&is=6961278f&hm=3bd97de2d2379eae68fea2845c2a0a24f03f964f8892c27263e72dca681257bb&=&format=webp&quality=lossless&width=350&height=350",
},
{
    "title": "Gravemark Reavers",
    "description": "Desecrators plunder burial grounds, guarded by crude undead constructs.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459217302070366360/content.png?ex=69627983&is=69612803&hm=df5eafc5ce4dc1b768dc13304e5b07c5c1df1367626531b5b6ff5c4ca1447224&=&format=webp&quality=lossless&width=839&height=839",
},
{
    "title": "Fogshard Elemental",
    "description": "Condensed mist crystallizes into a hostile elemental form.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459218213660524686/content.png?ex=69627a5d&is=696128dd&hm=41ac250a6067a6fbea1b1721caee817fe451b1b81d6feba048a1b0b46b4eb152&=&format=webp&quality=lossless",
},
{
    "title": "Moon-Scarred Hunter",
    "description": "A cursed tracker stalks prey under lunar influence, unable to stop.",
    "difficulty": "standard",
    "image": "https://media.discordapp.net/attachments/1459199810778300426/1459218730650304592/content.png?ex=69627ad8&is=69612958&hm=fc7c50608d4fa2c34e6810833567c5e833277e257087dc5562f0b08f500db348&=&format=webp&quality=lossless&width=350&height=350",
},


    # ────────────────
    # MAJOR THREATS
    # ────────────────
    {
        "title": "Rootbound Colossus",
        "description": "Ancient roots tear free from the earth, forming a towering guardian.",
        "difficulty": "major",
        "image": "https://media.discordapp.net/attachments/1459199810778300426/1459220676262101173/content.png?ex=69627ca8&is=69612b28&hm=9ac81cc4f88d64b8df210950e67658de53aaededb3f1b483cbda1659f4bfaa6c&=&format=webp&quality=lossless&width=350&height=350",
    },
    {
        "title": "Mistbound Behemoth",
        "description": "A massive silhouette moves within the fog, its footsteps shaking the vale.",
        "difficulty": "major",
        "image": "https://media.discordapp.net/attachments/1459199810778300426/1459221579081846865/content.png?ex=69627d7f&is=69612bff&hm=41d244c219a7a2e1b099fa7e07fe7734d68310736f976aecfb33f882384f9196&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "Gravetide Herald",
        "description": "A robed figure rings a rusted bell, raising the dead with each toll.",
        "difficulty": "major",
        "image": "https://media.discordapp.net/attachments/1459199810778300426/1459221890009665566/content.png?ex=69627dc9&is=69612c49&hm=327d66ac489f658a28043f4a51d353564580c47ec47e649d6a60c9a67fde8665&=&format=webp&quality=lossless",
    },
    {
        "title": "The Hollow Huntsman",
        "description": "A headless rider emerges from the mist, tracking those marked by fate.",
        "difficulty": "major",
        "image": "https://media.discordapp.net/attachments/1459199810778300426/1459224085044400188/content.png?ex=69627fd4&is=69612e54&hm=b08cc31fdfb96e637bf4c6d8ead76156e4f424f050d3604beb0a328a63ab81a9&=&format=webp&quality=lossless",
    },
    {
        "title": "Veins of the Vale",
        "description": "The land itself ruptures, spawning living stone and wrathful earth-spirits.",
        "difficulty": "major",
        "image": "https://media.discordapp.net/attachments/1459199810778300426/1459224532924498021/content.png?ex=6962803f&is=69612ebf&hm=d3050448fe0c8c5e174b4a809cae0cda5ac8f8b5647a6f4c91995a9392222a80&=&format=webp&quality=lossless&width=839&height=839",
    },

    # ────────────────
    # CRITICAL THREATS
    # ────────────────
    {
        "title": "Veilbreak Manifestation",
        "description": "Reality thins as something pushes through from beyond the veil.",
        "difficulty": "critical",
        "image": "https://media.discordapp.net/attachments/1459199810778300426/1459225193695281194/content.png?ex=696280dd&is=69612f5d&hm=eb5d4e319115e9fdf375d23a55849fdb1ad004526e11f88e74d1fdf596580823&=&format=webp&quality=lossless",
    },
    {
        "title": "The Mist Sovereign",
        "description": "A towering entity of fog and will claims dominion over the vale itself.",
        "difficulty": "critical",
        "image": "https://media.discordapp.net/attachments/1459199810778300426/1459225698563784714/content.png?ex=69628155&is=69612fd5&hm=42ddd7d2d68ce9ed619ad3569bd41ae93eb33204264030ea8260400139ea398f&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "Cataclysm Bloom",
        "description": "A massive arcane growth pulses violently, warping everything nearby.",
        "difficulty": "critical",
        "image": "https://media.discordapp.net/attachments/1459199810778300426/1459229773971587184/content.png?ex=69628521&is=696133a1&hm=907aa94b9177e174e0e90b90a2b3f4fceb1ba38d905ade6ccb9da1909dfb7966&=&format=webp&quality=lossless&width=839&height=839",
    },
    {
        "title": "Echo of a Slumbering Titan",
        "description": "A fragment of a greater being awakens, reshaping the land with each movement.",
        "difficulty": "critical",
        "image": "https://media.discordapp.net/attachments/1459199810778300426/1459231099623313478/content.png?ex=6962865d&is=696134dd&hm=c047c29b92c275d9966492ecd093a03e83e599e4df69976e59b88056d10813ec&=&format=webp&quality=lossless",
    },
    {
        "title": "The Veiled Catastrophe",
        "description": "An approaching calamity made manifest, heralding devastation if unchecked.",
        "difficulty": "critical",
        "image": "https://media.discordapp.net/attachments/1459199810778300426/1459231709982752972/content.png?ex=696286ee&is=6961356e&hm=c49bd37f4752c88034d1b1a98fd516dfbd6c4dde6bc79302f1d38a78f8789953&=&format=webp&quality=lossless&width=839&height=839",
    },
]

