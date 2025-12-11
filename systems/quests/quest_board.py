class QuestBoard:
    """
    Seasonal quest board tracker.
    Tracks global points for the guild.
    """
    def __init__(self):
        self.season_id = "default_season"
        self.global_points = 0

        # NEW: where the board is displayed
        self.display_channel_id: int | None = None
        self.message_id: int | None = None

    def add_points(self, amount: int):
        self.global_points += amount

    def reset_season(self, new_season_id: str):
        self.season_id = new_season_id
        self.global_points = 0
        # keep display info so the same message can be reused
