from __future__ import annotations
import discord


class WanderingEventView(discord.ui.View):
    def __init__(self, manager, event_id: str):
        super().__init__(timeout=None)
        self.manager = manager
        self.event_id = event_id

    @discord.ui.button(label="⚔️ Join the Hunt", style=discord.ButtonStyle.danger)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.manager.handle_participation(interaction, self.event_id)


class WanderingEventResolvedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Event Resolved",
                style=discord.ButtonStyle.gray,
                disabled=True
            )
        )
