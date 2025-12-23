from __future__ import annotations
import asyncio
import secrets
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Optional
import random
from .monsters import WANDERING_MONSTERS
import discord
from .models import WanderingEvent
from .views import WanderingEventView, WanderingEventResolvedView
from .storage import save_active_event, load_active_event
import quest_manager


EVENT_INTERVAL = 3 * 60 * 60  # 3 hours

DIFFICULTY_TABLE = {
    "test":    {"minutes": 5, "required": 1,  "faction": 5, "global": 5, "player": 1},
    "minor":    {"minutes": 15, "required": 3,  "faction": 10, "global": 10, "player": 1},
    "standard": {"minutes": 20, "required": 5,  "faction": 20, "global": 20, "player": 1},
    "major":    {"minutes": 30, "required": 8,  "faction": 30, "global": 25, "player": 1},
    "critical": {"minutes": 30, "required": 12, "faction": 40, "global": 30, "player": 1},
}

DIFFICULTY_SPAWN_WEIGHT = {
    "minor": 50,
    "standard": 25,
    "major": 10,
    "critical": 3,
    "test": 100,
}

def pick_random_monster(self):
    monsters = WANDERING_MONSTERS
    weights = [m["weight"] for m in monsters]
    return random.choices(monsters, weights=weights, k=1)[0]

async def scheduled_spawn_loop(self, bot):
    while True:
        await asyncio.sleep(EVENT_INTERVAL)

        if self.active and not self.active.resolved:
            continue

        monster = self.pick_random_monster()
        await self.spawn(
            bot=bot,
            title=monster["title"],
            description=monster["description"],
            difficulty=monster["difficulty"],
        )

class WanderingEventManager:
    def __init__(self, quest_manager, luneth_channel_id: int):
        self.quest_manager = quest_manager
        self.luneth_channel_id = luneth_channel_id

        self.active: Optional[WanderingEvent] = None
        self._resolve_task: Optional[asyncio.Task] = None

        self.refresh_board_callback = None

    # ---------- Embeds ----------
    def build_event_embed(self, event: WanderingEvent) -> discord.Embed:

        embed = discord.Embed(
            title=f"🐲 Wandering Threat: {event.title}",
            description=event.description,
            color=discord.Color.dark_purple(),
        )
        embed.add_field(name="Difficulty", value=event.difficulty.title(), inline=True)
        embed.add_field(name="⏳ Event Duration",value=f"{event.duration_minutes} minutes",inline=True,)
        embed.add_field(name="Participants",value=f"{len(event.participants)} / {event.required_participants}",inline=True)
        embed.set_footer(text="Join the hunt before it vanishes into the mist.")
        return embed

    def build_result_embed(self, event: WanderingEvent, success: bool) -> discord.Embed:
        color = discord.Color.green() if success else discord.Color.red()
        title = "✅ Threat Resolved!" if success else "❌ The Threat Fades…"

        embed = discord.Embed(
            title=title,
            description=f"**{event.title}**",
            color=color,
        )
        embed.add_field(
            name="Outcome",
            value="SUCCESS" if success else "FAILURE",
            inline=True
        )
        embed.add_field(
            name="Participants",
            value=f"{len(event.participants)} / {event.required_participants}",
            inline=True
        )

        if success:
            # list factions that earned
            factions = sorted(event.participating_factions)
            if factions:
                lines = [f"• **{fid}** +{event.faction_reward}" for fid in factions]
            else:
                lines = ["• (No factions recorded)"]

            embed.add_field(
                name="Rewards",
                value=(
                    f"🌍 Global Progress: **+{event.global_reward}**\n"
                    f"⚡ Faction Power Progress:\n" + "\n".join(lines) + "\n"
                ),
                inline=False
            )
        else:
            embed.add_field(
                name="Rewards",
                value="No progress gained. The Vale remains restless…",
                inline=False
            )

        embed.set_footer(text="This event will be cleared shortly.")
        return embed

    # ---------- Public API ----------
    async def startup_resume(self, bot: discord.Client):
        """Call on bot ready. Restores active event and re-schedules resolution."""
        self.active = load_active_event()
        if not self.active:
            return

        # If it already ended while bot was down, resolve immediately
        if datetime.now(timezone.utc) >= self.active.ends_at and not self.active.resolved:
            await self.resolve_active(bot)
            return

        # Otherwise schedule
        self._schedule_resolution(bot)

        # Also try to refresh the message view/embed (optional)
        await self._refresh_active_message(bot)

    async def spawn(self, bot: discord.Client, title: str, description: str, difficulty: str):
        if difficulty not in DIFFICULTY_TABLE:
            raise ValueError(f"Invalid difficulty: {difficulty}")

        # prevent stacking events
        if self.active and not self.active.resolved:
            raise RuntimeError("An event is already active.")

        cfg = DIFFICULTY_TABLE[difficulty]
        ends_at = datetime.now(timezone.utc) + timedelta(minutes=cfg["minutes"])

        event = WanderingEvent(
            event_id=secrets.token_hex(8),
            channel_id=self.luneth_channel_id,
            message_id=None,
            duration_minutes = cfg["minutes"],
            ends_at=ends_at,
            title=title,
            description=description,
            difficulty=difficulty,
            required_participants=cfg["required"],
            faction_reward=cfg["faction"],
            global_reward=cfg["global"],
        )
        self.active = event

        channel = bot.get_channel(self.luneth_channel_id) or await bot.fetch_channel(self.luneth_channel_id)
        msg = await channel.send(
            embed=self.build_event_embed(event),
            view=WanderingEventView(self, event.event_id),
        )

        event.message_id = msg.id
        save_active_event(event)

        self._schedule_resolution(bot)

    async def handle_participation(self, interaction: discord.Interaction, event_id: str):
        event = self.active
        if not event or event.event_id != event_id:
            return await interaction.response.send_message("⚠️ This event is no longer active.", ephemeral=True)

        if event.resolved or datetime.now(timezone.utc) >= event.ends_at:
            return await interaction.response.send_message("⚠️ This event has already ended.", ephemeral=True)

        user_id = interaction.user.id
        if user_id in event.participants:
            return await interaction.response.send_message("✅ You’re already in the hunt.", ephemeral=True)

        # Determine the player's faction from your existing system
        player = self.quest_manager.get_player(user_id)

        if user_id in event.participants:
            return await interaction.response.send_message(
                "✅ You’re already participating.",
                ephemeral=True,
            )

        event.participants.add(user_id)

        if player.faction_id:
            event.participating_factions.add(player.faction_id)

        save_active_event(event)

        await self._refresh_active_message(interaction.client)

        await interaction.response.send_message(
            "⚔️ You’ve joined the event!",
            ephemeral=True,
        )

    async def resolve_active(self, bot: discord.Client):
        event = self.active
        if not event or event.resolved:
            return

        success = len(event.participants) >= event.required_participants

        # Award points only on success
        if success:
            # 🌍 global ONCE
            self.quest_manager.quest_board.global_points += event.global_reward

            # ⚡ faction power per participating faction
            for fid in event.participating_factions:
                self.quest_manager.quest_board.faction_points[fid] = (
                    self.quest_manager.quest_board.faction_points.get(fid, 0) + event.faction_reward
                )


            # 🏅 player contribution per participant
            for uid in event.participants:
                p = self.quest_manager.get_player(uid)
                p.monsters_season += 1
                p.monsters_lifetime += 1

            self.quest_manager.save_board()
            self.quest_manager.save_players()

            # 🔄 Refresh the quest board embed
        if self.refresh_board_callback:
            await self.refresh_board_callback(bot)


        # Edit the event message to result state
        await self._edit_to_result(bot, success)

        event.resolved = True
        save_active_event(event)

        # Auto-delete after 10 minutes
        await self._schedule_delete(bot, delay_seconds=600)

        # Clear active
        self.active = None
        save_active_event(None)

    # ---------- Internals ----------
    def _schedule_resolution(self, bot: discord.Client):
        if self._resolve_task and not self._resolve_task.done():
            self._resolve_task.cancel()

        async def _runner():
            assert self.active is not None
            delay = (self.active.ends_at - datetime.now(timezone.utc)).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
            await self.resolve_active(bot)

        self._resolve_task = asyncio.create_task(_runner())

    async def _refresh_active_message(self, bot: discord.Client):
        event = self.active
        if not event or not event.message_id:
            return
        try:
            channel = bot.get_channel(event.channel_id) or await bot.fetch_channel(event.channel_id)
            msg = await channel.fetch_message(event.message_id)
            await msg.edit(embed=self.build_event_embed(event), view=WanderingEventView(self, event.event_id))
        except Exception:
            # silently ignore; message could be deleted
            pass

    async def _edit_to_result(self, bot: discord.Client, success: bool):
        event = self.active
        if not event or not event.message_id:
            return
        try:
            channel = bot.get_channel(event.channel_id) or await bot.fetch_channel(event.channel_id)
            msg = await channel.fetch_message(event.message_id)
            await msg.edit(embed=self.build_result_embed(event, success), view=WanderingEventResolvedView())
        except Exception:
            pass

    async def _schedule_delete(self, bot: discord.Client, delay_seconds: int = 600):
        event = self.active
        if not event or not event.message_id:
            return

        async def _deleter():
            await asyncio.sleep(delay_seconds)
            try:
                channel = bot.get_channel(event.channel_id) or await bot.fetch_channel(event.channel_id)
                msg = await channel.fetch_message(event.message_id)
                await msg.delete()
            except Exception:
                pass

        asyncio.create_task(_deleter())
