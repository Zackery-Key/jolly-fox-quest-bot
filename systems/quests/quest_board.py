class QuestBoard:
    """
    Seasonal quest board tracker.
    Tracks global points for the guild.
    """
    def __init__(self, global_points=0, season_id="default_season"):
        self.global_points = global_points
        self.season_id = season_id

    def add_points(self, amount: int):
        self.global_points += amount

    def reset_season(self, new_season_id: str):
        self.season_id = new_season_id
        self.global_points = 0
