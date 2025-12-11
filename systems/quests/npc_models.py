from dataclasses import dataclass

@dataclass
class NPC:
    npc_id: str
    name: str
    avatar_url: str = ""
    default_reply: str = ""

    def to_dict(self):
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "default_reply": self.default_reply
        }

    @staticmethod
    def from_dict(data: dict):
        return NPC(
            npc_id=data.get("npc_id"),
            name=data.get("name"),
            avatar_url=data.get("avatar_url", ""),
            default_reply=data.get("default_reply", "")
        )
