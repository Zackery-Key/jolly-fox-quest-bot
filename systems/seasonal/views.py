import discord
from systems.seasonal.state import get_season_state
from systems.quests.factions import FACTIONS
from systems.seasonal.state import register_vote
from systems.quests.quest_manager import get_member_faction_id


def build_seasonal_embed():
    state = get_season_state()
    boss = state["boss"]

    embed = discord.Embed(
        title=f"🌍 Seasonal Event — {boss['name']}",
        description=(
            f"**Phase:** {boss['phase']}\n"
            f"**HP:** {boss['hp']} / {boss['max_hp']}\n\n"
            "Each day, choose how your faction responds.\n"
            "_You may change your vote, but only one counts._"
        ),
        color=discord.Color.dark_green(),
    )

    for faction_id, faction in FACTIONS.items():
        votes = state["votes"].get(faction_id, {})
        atk = len(votes.get("attack", []))
        dfn = len(votes.get("defend", []))
        heal = len(votes.get("heal", []))

        embed.add_field(
            name=f"{faction.emoji} {faction.name}",
            value=(
                f"⚔️ Attack: **{atk}**\n"
                f"🛡️ Defend: **{dfn}**\n"
                f"💚 Heal: **{heal}**"
            ),
            inline=True,
        )

    embed.set_footer(text="Votes reset daily • Factionless members cannot vote")

    return embed



class SeasonalVoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _handle_vote(self, interaction: discord.Interaction, action: str):
        faction = get_member_faction_id(interaction.user)

        if not faction:
            return await interaction.response.send_message(
                "❌ You must belong to a faction to participate.",
                ephemeral=True,
            )

        state = get_season_state()
        success = register_vote(
            state,
            interaction.user.id,
            faction,
            action,
        )

        if not success:
            return await interaction.response.send_message(
                "❌ Could not register your vote.",
                ephemeral=True,
            )

        # Update the embed in-place
        await interaction.message.edit(embed=build_seasonal_embed(), view=self)

        await interaction.response.send_message(
            f"🗳️ Vote recorded: **{action.title()}**",
            ephemeral=True,
        )

    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, "attack")

    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.primary)
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, "defend")

    @discord.ui.button(label="💚 Heal", style=discord.ButtonStyle.success)
    async def heal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, "heal")