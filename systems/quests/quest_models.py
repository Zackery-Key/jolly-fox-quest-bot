from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class QuestType(str, Enum):
    SKILL = "SKILL"
    SOCIAL = "SOCIAL"
    FETCH = "FETCH"
    TRAVEL = "TRAVEL"


@dataclass
class QuestTemplate:
    quest_id: str                     # unique internal ID
    name: str                         # quest name shown to players
    type: QuestType                   # SKILL | SOCIAL | FETCH | TRAVEL
    points: int                       # default points on completion

    # CHANNEL REQUIREMENTS (vary by type)
    required_channel_id: Optional[int] = None       # SOCIAL, SKILL
    source_channel_id: Optional[int] = None         # FETCH only
    turnin_channel_id: Optional[int] = None         # FETCH only

    # SKILL QUEST FIELDS
    dc: Optional[int] = None
    points_on_success: Optional[int] = None
    points_on_fail: Optional[int] = None

    # SOCIAL QUEST FIELDS
    npc_id: Optional[str] = None

    # FETCH QUEST FIELDS
    item_name: Optional[str] = None

    # QUEST TEXT
    summary: str = ""
    details: str = ""

    # OPTIONAL tags for filtering (not required)
    tags: List[str] = field(default_factory=list)
