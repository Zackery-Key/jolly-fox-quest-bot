from dataclasses import dataclass, field
from typing import List, Dict
import random
from systems.quests.quest_models import QuestType, QuestTemplate

@dataclass
class NPC:
    npc_id: str
    name: str
    avatar_url: str = ""

    # NEW optional expanded dialogue features
    greetings: List[str] = field(default_factory=list)
    idle_lines: List[str] = field(default_factory=list)
    quest_dialogue: Dict[str, List[str]] = field(default_factory=dict)

    # Legacy fallback support
    default_reply: str = ""

    # Optional flavor
    personality: str = ""

    def get_npc_quest_dialogue(npc, quest, *, success=None):
        if not npc or not quest:
            return "The NPC glances at you silently."

        quest_id = getattr(quest, "quest_id", None)
        quest_type = quest.type.value if isinstance(quest.type, QuestType) else quest.type

        # Priority 1: quest-specific
        if quest_id and quest_id in npc.quest_dialogue:
            return random.choice(npc.quest_dialogue[quest_id])

        # Priority 2: SKILL outcomes
        if quest_type == "SKILL" and success is not None:
            key = "SKILL_SUCCESS" if success else "SKILL_FAIL"
            if key in npc.quest_dialogue:
                return random.choice(npc.quest_dialogue[key])

        # Priority 3: type-level fallback
        if quest_type in npc.quest_dialogue:
            return random.choice(npc.quest_dialogue[quest_type])

        return npc.default_reply or "The NPC nods without a word."


    def to_dict(self):
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "greetings": self.greetings,
            "idle_lines": self.idle_lines,
            "quest_dialogue": self.quest_dialogue,
            "default_reply": self.default_reply,
            "personality": self.personality
        }

    @staticmethod
    def from_dict(data: dict):
        return NPC(
            npc_id=data.get("npc_id"),
            name=data.get("name"),
            avatar_url=data.get("avatar_url", ""),

            greetings=data.get("greetings", []),
            idle_lines=data.get("idle_lines", []),
            quest_dialogue=data.get("quest_dialogue", {}),

            default_reply=data.get("default_reply", ""),
            personality=data.get("personality", "")
        )
