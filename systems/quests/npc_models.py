from dataclasses import dataclass


@dataclass
class NPC:
    npc_id: str                # "celara", "orlin", etc.
    name: str                  # Display name
    avatar_url: str            # Image for embeds
    default_reply: str         # NPC flavor text
