import discord
from systems.seasonal.state import get_season_state
from systems.quests.factions import FACTIONS
from systems.seasonal.state import register_vote
from systems.quests.factions import get_member_faction_id


def build_seasonal_embed():
    state = get_season_state()
    boss = state["boss"]

    # ✅ Create embed FIRST
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

    # ✅ THEN set thumbnail
    if boss.get("avatar_url"):
        embed.set_thumbnail(url=boss["avatar_url"])

    # Faction vote breakdown
    for faction_id, faction in FACTIONS.items():
        votes = state["votes"].get(faction_id, {})
        atk = len(votes.get("attack", []))
        dfn = len(votes.get("defend", []))
        heal = len(votes.get("heal", []))
        pwr = len(votes.get("power", []))

        # faction HP display (if exists)
        fh = state.get("faction_health", {}).get(faction_id, {})
        fhp = fh.get("hp", 0)
        fmax = fh.get("max_hp", 0)

        fp = state["faction_powers"].get(faction_id, {})
        power_status = (
            "❌ Used"
            if fp.get("used")
            else "⚡ Ready"
            if fp.get("unlocked")
            else "🔒 Locked"
        )

        embed.add_field(
            name=f"{faction.emoji} {faction.name}",
            value=(
                f"❤️ HP: **{fhp} / {fmax}**\n"
                f"⚔️ Attack: **{atk}**\n"
                f"🛡️ Defend: **{dfn}**\n"
                f"💚 Heal: **{heal}**\n"
                f"⚡ Power: **{pwr}** ({power_status})"
            ),
            inline=True,
        )

    embed.set_footer(text="Votes reset daily • Factionless members cannot vote")

    return embed



class SeasonalVoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self._update_power_button_state()

    def _update_power_button_state(self):
        state = get_season_state()
        powers = state.get("faction_powers", {})

        # Default: enabled
        disable = False
        label = "⚡ Power"

        # If ALL faction powers are either unused but unlocked OR used?
        # We disable per-user in handler, but globally disable if power is spent.
        for fp in powers.values():
            if fp.get("used"):
                disable = True
                label = "⚡ Power (Used)"
                break

        # Find the power button and update it
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label.startswith("⚡"):
                item.disabled = disable
                item.label = label


    async def _handle_vote(self, interaction: discord.Interaction, action: str):
        faction = get_member_faction_id(interaction.user)

        if not faction:
            return await interaction.response.send_message(
                "❌ You must belong to a faction to participate.",
                ephemeral=True,
            )

        state = get_season_state()

        # ❌ Block power vote if not allowed
        if action == "power":
            fp = state["faction_powers"].get(faction)

            if not fp or not fp.get("unlocked"):
                return await interaction.response.send_message(
                    "❌ Your faction has not unlocked its power yet.",
                    ephemeral=True,
                )

            if fp.get("used"):
                return await interaction.response.send_message(
                    "❌ Your faction’s power has already been used this season.",
                    ephemeral=True,
                )

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

    @discord.ui.button(label="⚡ Power", style=discord.ButtonStyle.secondary)
    async def power(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, "power")
