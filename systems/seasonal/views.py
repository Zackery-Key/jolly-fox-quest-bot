import discord
from systems.seasonal.state import get_season_state
from systems.quests.factions import FACTIONS
from systems.seasonal.state import register_vote
from systems.quests.factions import get_member_faction_id


def build_seasonal_embed():
    state = get_season_state()
    boss = state["boss"]
    difficulty = state.get("difficulty", "normal").title()
    day = int(state.get("day", 1))
    max_days = int(state.get("max_days", 0) or 0)
    day_line = f"**Day:** {day} / {max_days}\n" if max_days > 0 else ""
    boss_type = state.get("boss_type", "seasonal")

    # 🏁 Ended state
    if not state.get("active"):
        reason = state.get("ended_reason")

        if reason == "boss_defeated":
            title = f"🏆 Seasonal Event — {boss['name']}"
            desc = (
                "The boss has been defeated.\n\n"
                "**Victory for the guild!**"
            )
            color = discord.Color.gold()

        elif reason == "time_expired":
            title = f"⏳ Seasonal Event — {boss['name']}"
            desc = (
                "Time has expired.\n\n"
                "**The boss endures — and the guild must regroup.**"
            )
            color = discord.Color.dark_red()
        else:
            title = f"💀 Seasonal Event — {boss['name']}"
            desc = (
                "All factions have fallen.\n\n"
                "**The boss reigns supreme.**"
            )
            color = discord.Color.dark_red()

        embed = discord.Embed(title=title, description=desc, color=color)

        if boss.get("avatar_url"):
            embed.set_thumbnail(url=boss["avatar_url"])

        return embed

    # ✅ Create embed FIRST
    label = "🟡 Minor Boss" if boss_type == "minor" else "🔴 Seasonal Boss"

    embed = discord.Embed(
        title=f"{label} — {boss['name']}",
        description=(
            f"**Threat Level:** {difficulty}\n"
            f"{day_line}"
            f"**HP:** {boss['hp']} / {boss['max_hp']}\n\n"
            "Each day, choose how you and your faction responds.\n"
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

        default_action = {
            "spellfire": "attack",
            "shieldborne": "defend",
            "verdant": "heal",
        }.get(faction_id)

        eff_atk, eff_dfn, eff_heal = atk, dfn, heal
        if default_action == "attack":
            eff_atk += pwr
        elif default_action == "defend":
            eff_dfn += pwr
        elif default_action == "heal":
            eff_heal += pwr

        # Optional “incl. X power” text only on the default action line
        atk_note = f" _(incl. {pwr} power)_" if (default_action == "attack" and pwr > 0) else ""
        dfn_note = f" _(incl. {pwr} power)_" if (default_action == "defend" and pwr > 0) else ""
        heal_note = f" _(incl. {pwr} power)_" if (default_action == "heal" and pwr > 0) else ""

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
                f"⚔️ Attack: **{eff_atk}**{atk_note}\n"
                f"🛡️ Defend: **{eff_dfn}**{dfn_note}\n"
                f"💚 Heal: **{eff_heal}**{heal_note}\n"
                f"⚡ Power: **{pwr}** ({power_status})\n"
                + (f"_Power votes also count as **{default_action}** today._" if default_action else "")
            ),
            inline=True,
        )

    embed.set_footer(text="Votes reset daily • Factionless members cannot vote")

    return embed

class SeasonalVoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


    async def _handle_vote(self, interaction: discord.Interaction, action: str):    
        state = get_season_state()

        if not state.get("active"):
            return await interaction.response.send_message(
                "⚠️ This seasonal event has ended.",
                ephemeral=True,
            )
        
        faction = get_member_faction_id(interaction.user)

        alive = state.get("alive_factions", set())

        if faction not in alive:
            return await interaction.response.send_message(
                "💀 Your faction was defeated in a previous battle and cannot act.",
                ephemeral=True,
            )

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

class SeasonalEndedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="Event Ended", style=discord.ButtonStyle.secondary, disabled=True)
    async def ended(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass
