# ========= Imports =========

import os
import random
import discord
from discord.ext import commands
import io
import json
import asyncio
from datetime import datetime, timedelta, timezone
from systems.seasonal.state import BASE_ATTACK_DAMAGE
from systems.seasonal.views import SeasonalEndedView
from systems.seasonal.state import (
    get_season_state,
    resolve_daily_boss,
    reset_votes_for_new_day,
    reset_season_state,
)
from systems.seasonal.storage import save_season
from systems.seasonal.views import build_seasonal_embed, SeasonalVoteView
from systems.quests.factions import FACTION_ROLE_IDS

from systems.quests.npc_models import get_npc_quest_dialogue
from systems.quests.quest_manager import QuestManager
from systems.quests.quest_models import QuestType, QuestTemplate
from systems.quests.factions import get_faction, FACTIONS
from systems.quests.npc_models import NPC
from systems.quests import storage
from systems.quests.storage import QUESTS_FILE
from discord import app_commands
from datetime import date
from systems.seasonal.views import build_seasonal_embed, SeasonalVoteView
from systems.seasonal.state import get_season_state
from systems.quests.factions import get_member_faction_id
from systems.seasonal.storage import load_season, save_season
from systems.badges.definitions import BADGES
from systems.quests.quest_manager import evaluate_join_date_badges
from discord import app_commands
from systems.quests.wandering import WanderingEventManager
from typing import Literal
from datetime import datetime, timedelta, timezone


# ========= Constants / IDs =========

# Env
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))
POINTS_LOG_CHANNEL_ID = int(os.getenv("POINTS_LOG_CHANNEL_ID", 0))
BADGE_ANNOUNCE_CHANNEL_ID = int(os.getenv("BADGE_ANNOUNCE_CHANNEL_ID", 0))
GRIMBALD_ROLE_ID = int(os.getenv("GRIMBALD_ROLE_ID"))
TAVERN_CHANNEL_ID = int(os.getenv("TAVERN_CHANNEL_ID", 0))
LUNETH_VALE_CHANNEL_ID = int(os.getenv("LUNETH_VALE_CHANNEL_ID", 0))
WANDERING_PING_ROLE_ID = int(os.getenv("WANDERING_PING_ROLE_ID", 0))
QUEST_POINTS = 5

# Quest Manager
quest_manager = QuestManager()
print("QUEST MANAGER INITIALIZED")

wandering_manager = WanderingEventManager(
    quest_manager=quest_manager,
    luneth_channel_id=LUNETH_VALE_CHANNEL_ID,
)

if not TOKEN or not GUILD_ID:
    raise ValueError("Missing DISCORD_TOKEN or GUILD_ID environment variable.")


# ========= Bot Setup =========

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
npc_webhook_cache: dict[int, discord.Webhook] = {}

bot = commands.Bot(command_prefix="!", intents=intents)



# ========= Shared Helpers =========

async def update_seasonal_embed(bot):
    state = get_season_state()
    embed_info = state.get("embed", {})

    channel_id = embed_info.get("channel_id")
    message_id = embed_info.get("message_id")

    if not channel_id or not message_id:
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        return

    try:
        message = await channel.fetch_message(message_id)

        # 🧠 Choose view based on event state
        view = SeasonalVoteView() if state.get("active") else SeasonalEndedView()

        await message.edit(
            embed=build_seasonal_embed(),
            view=view,
        )

    except Exception as e:
        print(f"[SEASON] Failed to update embed: {e}")

def estimate_expected_daily_votes(
    guild: discord.Guild,
    participation_rate: float = 0.35,
) -> int:
    """
    Estimate total daily votes based on faction role sizes.
    """
    total_members = 0

    for faction_id, role_id in FACTION_ROLE_IDS.items():
        if not role_id:
            continue

        role = guild.get_role(role_id)
        if role:
            total_members += len(role.members)


    # Safety floor so small servers don’t break
    return max(10, int(total_members * participation_rate))

async def seasonal_midnight_loop(bot: discord.Client):
    await bot.wait_until_ready()

    while not bot.is_closed():
        await sleep_until_midnight_utc()

        state = get_season_state()

        # Do nothing if season is inactive
        if not state.get("active"):
            continue

        # 🔥 Resolve the day
        summary = resolve_daily_boss(state)

        # 🔄 Reset votes for the new day
        reset_votes_for_new_day(state)

        # 💾 Persist state
        save_season(state)

        # 🖼️ Update embed if it exists
        embed_info = state.get("embed", {})
        channel_id = embed_info.get("channel_id")
        message_id = embed_info.get("message_id")

        if channel_id and message_id:
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    await message.edit(
                        embed=build_seasonal_embed(),
                        view=SeasonalVoteView(),
                    )
                except Exception as e:
                    print(f"[SEASON] Failed to update embed: {e}")

def initialize_season_boss_and_factions(
    state: dict,
    expected_votes: int,
    target_days: int = 7,
):

    # Assume not all votes are attacks
    expected_attack_votes = max(1, int(expected_votes * 0.45))

    # 🐉 Boss HP = expected throughput × target days
    boss_hp = int(expected_attack_votes * BASE_ATTACK_DAMAGE * target_days * 1.4)
    boss_hp = max(500, boss_hp)

    state["boss"]["hp"] = boss_hp
    state["boss"]["max_hp"] = boss_hp
    state["boss"]["phase"] = 1

    # Faction HP should survive ~2–3 strong retaliation hits
    FACTION_HP_MULTIPLIER = 60  # safe, tunable

    faction_hp = max(
        300,
        expected_attack_votes * FACTION_HP_MULTIPLIER
    )


    for fid in state["faction_health"]:
        state["faction_health"][fid]["hp"] = faction_hp
        state["faction_health"][fid]["max_hp"] = faction_hp

    # Reset faction power usage
    for fp in state["faction_powers"].values():
        fp["used"] = False

    # Mark season active
    state["active"] = True
    state["day"] = 1


def make_progress_bar(value: int, max_value: int, length: int = 20) -> str:
    """Simple text progress bar for embeds."""
    if max_value <= 0:
        max_value = 1

    ratio = max(0.0, min(1.0, value / max_value))
    filled = int(ratio * length)
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}]"

def get_crown_holder(faction_points: dict[str, int]) -> str | None:
    if not faction_points:
        return None
    return max(faction_points.items(), key=lambda x: x[1])[0]

def build_board_embed():
    """Build the quest board embed including faction standings."""
    stats = quest_manager.get_scoreboard()
    board = quest_manager.quest_board

    global_points = stats["global_points"]
    season_completed = stats["season_quest_completed"]
    monsters_completed = stats["season_monsters_completed"]

    # Use board.season_goal but default to 100 if something weird
    season_goal = board.season_goal if getattr(board, "season_goal", 0) > 0 else 100
    progress_bar = make_progress_bar(global_points, season_goal)

    # Build description including season name + reward text
    desc_lines = [f"Season: **{board.season_id}**"]
    desc_lines.append(f"Season Goal: **{season_goal}** guild points")

    reward_text = getattr(board, "season_reward", "") or "TBD"
    desc_lines.append(f"Season Reward: {reward_text}")

    embed = discord.Embed(
        title="🛡️ Jolly Fox Guild Quest Board",
        description="\n".join(desc_lines),
        color=discord.Color.gold(),
    )

    # Global progress
    # Prevent division by zero
    if season_goal > 0:
        pct = (global_points / season_goal) * 100
    else:
        pct = 0

    pct_text = f"{pct:.1f}%"  # one decimal place, e.g., 4.2%

    embed.add_field(
        name="📊 Global Guild Points",
        value=(
            f"{global_points} / {season_goal} pts "
            f"(**{pct_text}**)\n"
            f"{progress_bar}"
        ),
        inline=False,
    )

    embed.add_field(
        name="⚡ Faction Power Progress",
        value=(
            "Each faction advances independently.\n"
            "Reaching the goal unlocks a **one-time faction power** for the final boss."
        ),
        inline=False,
    )

    # Faction standings
    faction_points = board.faction_points or {}

    faction_goal = board.faction_goal if getattr(board, "faction_goal", 0) > 0 else 250

    for faction_id, fac in FACTIONS.items():
        pts = faction_points.get(faction_id, 0)
        bar = make_progress_bar(pts, faction_goal)

        unlocked = pts >= faction_goal
        status = " ⚡ **UNLOCKED**" if unlocked else ""

        embed.add_field(
            name=f"{fac.emoji} {fac.name}",
            value=f"{pts} / {faction_goal} pts{status}\n{bar}",
            inline=False,
        )

    crown_holder = get_crown_holder(faction_points)
    if crown_holder:
        embed.add_field(
            name="👑 Crown Holder",
            value=FACTIONS[crown_holder].name,
            inline=False,
        )

    # Quest counts
    embed.add_field(
        name="🏆 Quests Completed This Season",
        value=str(season_completed),
        inline=False,
    )

    embed.add_field(
        name="🐲 Wandering Threats Cleared",
        value=str(monsters_completed),
        inline=False,
    )
    
    embed.set_footer(
        text="You get one quest a day and they reset at 00:00 UTC"
    )

    return embed

def build_profile_embed(
    viewer: discord.Member,
    target: discord.Member,
    player
) -> discord.Embed:
    """Build a public-facing guild profile embed."""

    level = player.level
    xp = player.xp
    next_xp = player.next_level_xp

    # XP Progress Bar
    filled = int((xp / next_xp) * 10) if next_xp > 0 else 0
    bar = "█" * filled + "░" * (10 - filled)

    # 🎖️ Active Title
    title_text = f"**{player.title}**" if player.title else "_None_"

    # Faction info
    faction = get_faction(player.faction_id)
    faction_name = faction.name if faction else "None"
    faction_icon = faction.emoji if faction else "❔"

    # 🏅 Badges
    if player.badges:
        badge_lines = []
        for badge_id in sorted(player.badges):
            badge = BADGES.get(badge_id)
            if badge:
                badge_lines.append(
                    f"{badge['emoji']} **{badge['name']}**"
                )
        badge_text = "\n".join(badge_lines)
    else:
        badge_text = "_No badges yet_"



    # Daily quest (public-safe)
    dq = player.daily_quest
    if dq.get("quest_id"):
        tmpl = quest_manager.get_template(dq["quest_id"])
        status = "Completed" if dq.get("completed") else "Active"
        dq_text = f"{tmpl.name} ({status})" if tmpl else "Unknown quest"
    else:
        dq_text = "No quest today"

    # Inventory visibility
    if viewer.id == target.id and player.inventory:
        inv_lines = [
            f"- **{name}** × {qty}"
            for name, qty in player.inventory.items()
        ]
        inv_text = "\n".join(inv_lines)
    elif viewer.id == target.id:
        inv_text = "_Empty_"
    else:
        inv_text = "_Private_"

    embed = discord.Embed(
        title=f"🦊 {target.display_name} — Guild Profile",
        color=discord.Color.orange(),
    )

    embed.set_thumbnail(url=target.display_avatar.url)
    
    embed.add_field(
        name="🎖️ Title",
        value=title_text,
        inline=False,
    )

    embed.add_field(
        name="📘 Level & Experience",
        value=(
            f"**Level:** {level}\n"
            f"**XP:** {xp} / {next_xp}\n"
            f"`{bar}`"
        ),
        inline=False,
    )

    embed.add_field(
        name="🏅 Faction",
        value=f"{faction_icon} **{faction_name}**",
        inline=False,
    )

    embed.add_field(
        name="🏆 Quest Completion",
        value=(
            f"**Seasonal Completed:** {player.season_completed}\n"
            f"**Lifetime Completed:** {player.lifetime_completed}"
        ),
        inline=False,
    )

    embed.add_field(
        name="🏅 Badges",
        value=badge_text,
        inline=False,
    )

    embed.add_field(
        name="🐲 Wandering Threats Cleared",
        value=(
            f"**Seasonal Completed:** {player.monsters_season}\n"
            f"**Lifetime Completed:** {player.monsters_lifetime}"
        ),
        inline=False,
    )

    embed.add_field(
        name="🎯 Daily Quest",
        value=dq_text,
        inline=False,
    )

    embed.add_field(
        name="🎒 Inventory",
        value=inv_text,
        inline=False,
    )

    embed.set_footer(text="Jolly Fox Guild — Adventure Awaits")

    return embed

async def refresh_quest_board(bot: commands.Bot):
    board = quest_manager.quest_board

    if not board.display_channel_id or not board.message_id:
        return

    try:
        channel = bot.get_channel(board.display_channel_id)
        if channel is None:
            channel = await bot.fetch_channel(board.display_channel_id)

        msg = await channel.fetch_message(board.message_id)
        embed = build_board_embed()
        await msg.edit(embed=embed, view=QuestBoardView())

        # --------------------------------------------------
        # 🔄 SYNC FACTION POWER UNLOCKS → SEASONAL STATE
        # --------------------------------------------------
        state = get_season_state()
        changed = False

        for faction_id, points in board.faction_points.items():
            if (
                points >= board.faction_goal
                and not state["faction_powers"][faction_id]["unlocked"]
            ):
                state["faction_powers"][faction_id]["unlocked"] = True
                changed = True

        if changed:
            save_season(state)

            # If a seasonal boss is active, update its embed immediately
            if state.get("active"):
                await update_seasonal_embed(bot)

    except discord.NotFound:
        # 🔥 AUTO-HEAL: message was deleted
        print("⚠ Quest board message missing. Clearing anchor.")

        board.display_channel_id = None
        board.message_id = None
        quest_manager.save_board()

    except discord.Forbidden as e:
        print("⚠ Quest board forbidden:", e)

    except Exception as e:
        print("⚠ Failed to refresh quest board:", e)

async def _ensure_active_daily(interaction, expected_type=None, create_if_missing=True):
    user = interaction.user
    user_id = user.id

    if create_if_missing:
        player = quest_manager.get_or_create_player(user_id)
    else:
        player = quest_manager.get_player(user_id)

    if not player:
        await interaction.followup.send(
            "You do not have a guild profile yet. Use `/quest` to begin.",
            ephemeral=True,
        )
        return None, None

    if not player.daily_quest:
        await interaction.followup.send(
            "🦊 You don't have an active quest today. Use `/quest` first.",
            ephemeral=True,
        )
        return None, None

    if "quest_id" not in player.daily_quest:
        await interaction.followup.send(
            "⚠️ Your daily quest data is incomplete. Use `/quest` to refresh.",
            ephemeral=True,
        )
        return None, None

    if player.daily_quest.get("completed"):
        await interaction.followup.send(
            "✅ You've already completed today's quest.",
            ephemeral=True,
        )
        return None, None

    quest_id = player.daily_quest.get("quest_id")
    template = quest_manager.get_template(quest_id)

    if template is None:
        await interaction.followup.send(
            "⚠️ Error: Your quest template could not be found. Please tell an admin.",
            ephemeral=True,
        )
        return None, None

    # Type check (SKILL/SOCIAL/FETCH/TRAVEL)
    if expected_type is not None and template.type != expected_type:
        await interaction.followup.send(
            f"❌ Your current quest is `{template.type.value}`, "
            f"not `{expected_type.value}`.\nUse the correct command for your quest type.",
            ephemeral=True,
        )
        return None, None

    # -----------------------------------------
    # NEW: Allowed role enforcement (Option B)
    # -----------------------------------------
    allowed_roles = getattr(template, "allowed_roles", []) or []

    # If quest has role restrictions, we enforce them:
    if allowed_roles:
        current_roles = {role.id for role in getattr(user, "roles", [])}
        snapshot = player.daily_quest.get("role_snapshot") or []

        # If they currently have at least one required role → OK
        if any(rid in current_roles for rid in allowed_roles):
            pass  # allowed
        else:
            # They do NOT currently have allowed roles.
            # Option B: If they had the role at assignment time, still allow completion.
            if any(rid in snapshot for rid in allowed_roles):
                # They were legit when the quest was assigned.
                pass
            else:
                # They never had the required roles for this quest.
                # This should not happen anymore with the new assignment logic,
                # but we handle it gracefully.
                await interaction.followup.send(
                    "❌ You don't have the required role to complete this quest.\n"
                    "If you believe this is a mistake, please contact an admin.\n"
                    "You will get a new quest tomorrow with `/quest`.",
                    ephemeral=True,
                )
                return None, None

    return player, template

def validate_quest_data(quests: dict) -> tuple[bool, str]:
    """Validate quest JSON before import."""

    for qid, q in quests.items():
        if not isinstance(q, dict):
            return False, f"Quest '{qid}' must be an object."

        # Required fields
        required = ["quest_id", "name", "type"]
        for field in required:
            if field not in q:
                return False, f"Quest '{qid}' missing required field '{field}'."

        # Validate type
        if q["type"] not in QuestType.__members__:
            return False, f"Quest '{qid}' has invalid type '{q['type']}'."

        t = q["type"]

        # Type-specific validation
        if t == "SOCIAL":
            if "npc_id" not in q:
                return False, f"Social quest '{qid}' missing npc_id."

        if t == "FETCH":
            for f in ["item_name", "source_channel_id", "turnin_channel_id"]:
                if f not in q:
                    return False, f"Fetch quest '{qid}' missing '{f}'."

        if t == "SKILL":
            if "dc" not in q:
                return False, f"Skill quest '{qid}' missing dc."


        if t == "TRAVEL":
            if "required_channel_id" not in q:
                return False, f"Travel quest '{qid}' missing required_channel_id."

    return True, "OK"

def validate_npc_data(npcs: dict) -> tuple[bool, str]:
    for npc_id, n in npcs.items():
        if not isinstance(n, dict):
            return False, f"NPC '{npc_id}' must be an object."

        if "npc_id" not in n or "name" not in n:
            return False, f"NPC '{npc_id}' missing npc_id or name."

        # Validate lists/dicts
        if "greetings" in n and not isinstance(n["greetings"], list):
            return False, f"NPC '{npc_id}' greetings must be a list."

        if "idle_lines" in n and not isinstance(n.get("idle_lines", []), list):
            return False, f"NPC '{npc_id}' idle_lines must be a list."

        if "quest_dialogue" in n and not isinstance(n["quest_dialogue"], dict):
            return False, f"NPC '{npc_id}' quest_dialogue must be a dict."

    return True, "OK"

async def send_daily_quest(interaction: discord.Interaction):
    user = interaction.user
    user_id = user.id
    today = str(date.today())

    # Get or create player FIRST
    player = quest_manager.get_or_create_player(user_id)

    # 🛑 HARD STOP — already completed today
    if (
        player.daily_quest
        and player.daily_quest.get("assigned_date") == today
        and player.daily_quest.get("completed")
    ):
        tmpl = quest_manager.get_template(player.daily_quest.get("quest_id"))

        await interaction.followup.send(
            (
                "✅ **You've already completed today's quest!**\n\n"
                f"**Quest:** {tmpl.name if tmpl else 'Unknown'}\n\n"
                "🕒 Come back tomorrow for a new one."
            ),
            ephemeral=True,
        )
        return

    # 📜 If they already have an active daily today, just show it
    if (
        player.daily_quest
        and player.daily_quest.get("assigned_date") == today
        and not player.daily_quest.get("completed")
    ):
        quest_id = player.daily_quest.get("quest_id")
    else:
        # ✅ SAFE: assign a new daily quest
        role_ids = [role.id for role in getattr(user, "roles", [])]
        quest_id = quest_manager.assign_daily(user_id, role_ids)

        if quest_id is None:
            await interaction.followup.send(
                "🦊 There are no quests available for your current roles right now.\n\n"
                "If you join a new guild faction or RP group later today, "
                "you can try again.",
                ephemeral=True,
            )
            return

    template = quest_manager.get_template(quest_id)
    if template is None:
        await interaction.followup.send(
            "⚠️ Error loading your quest. Please contact an admin.",
            ephemeral=True,
        )
        return

    completed = bool(player.daily_quest.get("completed"))
    status_label = "✅ COMPLETED" if completed else "🟠 ACTIVE"

    body = f"**Name:** {template.name}\n"

    if template.type == QuestType.SKILL:
        body += f"**Success:** {QUEST_POINTS or 0} pts\n"
        body += f"**Fail:** {QUEST_POINTS or 0} pts\n\n"
    else:
        body += f"**Points:** {QUEST_POINTS}\n\n"

    body += f"**Summary:** {template.summary}\n"

    hint_lines: list[str] = []

    if template.type == QuestType.SOCIAL:
        hint_lines.append(
            f"• Go to <#{template.required_channel_id}> and use `/talk`."
        )
        if template.npc_id:
            hint_lines.append(f"• Required NPC: `{template.npc_id}`")

    elif template.type == QuestType.SKILL:
        hint_lines.append(
            f"• Go to <#{template.required_channel_id}> and use `/skill`."
        )
        if template.dc:
            hint_lines.append(f"• Target DC: **{template.dc}**")

    elif template.type == QuestType.TRAVEL:
        hint_lines.append(
            f"• Go to <#{template.required_channel_id}> and use `/checkin`."
        )

    elif template.type == QuestType.FETCH:
        hint_lines.append(
            f"• Go to <#{template.source_channel_id}> and gather the item with `/fetch`, "
            f"then deliver to <#{template.turnin_channel_id}> and use `/turnin`."
        )
        if template.item_name:
            hint_lines.append(f"• Required item: **{template.item_name}**")

    hint_text = (
        "\n\n**How to complete it:**\n" + "\n".join(hint_lines)
        if hint_lines
        else ""
    )

    footer = (
        "\n\n✨ You’ve already completed this quest today."
        if completed
        else "\n\n✨ Complete this quest to earn guild points."
    )

    msg = (
        f"**🦊 Your Daily Quest — {status_label}**\n\n"
        + body
        + hint_text
        + footer
    )

    await interaction.followup.send(msg, ephemeral=True)

class QuestBoardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🦊 View Daily Quest",
        style=discord.ButtonStyle.primary,
        custom_id="quest_board:view_daily"
    )
    async def view_daily(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        await send_daily_quest(interaction)

    @discord.ui.button(
        label="📘 View Profile",
        style=discord.ButtonStyle.secondary,
        custom_id="quest_board:view_profile"
    )
    async def view_profile(self, interaction: discord.Interaction, button):

        await interaction.response.defer(ephemeral=True)

        player = quest_manager.get_or_create_player(interaction.user.id)
        embed = build_profile_embed(
            viewer=interaction.user,
            target=interaction.user,
            player=player,
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="🔔 Wandering Alerts",
        style=discord.ButtonStyle.secondary,
        custom_id="quest_board:toggle_wandering_alerts",
    )
        
    async def toggle_wandering_alerts(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not interaction.guild:
            return await interaction.response.send_message(
                "⚠️ This can only be used in a server.",
                ephemeral=True,
            )

        role = interaction.guild.get_role(WANDERING_PING_ROLE_ID)
        if not role:
            return await interaction.response.send_message(
                "⚠️ Alert role not configured.",
                ephemeral=True,
            )

        member = interaction.user

        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(
                "🔕 Wandering threat alerts **disabled**.",
                ephemeral=True,
            )
        else:
            await member.add_roles(role)
            await interaction.response.send_message(
                "🔔 Wandering threat alerts **enabled**!",
                ephemeral=True,
            )


def require_admin(interaction: discord.Interaction) -> bool:
    return interaction.user.guild_permissions.manage_guild

async def send_npc_response(
    interaction: discord.Interaction,
    npc,
    dialogue: str,
    title: str,
    footer: str | None = None,
    color: discord.Color = discord.Color.blurple(),
):
    embed = discord.Embed(
        title=title,
        description=f"> {dialogue}",
        color=color,
    )

    if npc:
        embed.set_author(
            name=npc.name,
            icon_url=npc.avatar_url if npc.avatar_url else discord.Embed.Empty,
        )

    if footer:
        embed.add_field(name="\u200b", value=footer, inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True
)

async def log_admin_action(bot, message: str):
    channel = bot.get_channel(POINTS_LOG_CHANNEL_ID)
    if channel:
        await channel.send(message)

def dict_autocomplete(source_dict, label_fn=None):
    async def _autocomplete(interaction, current: str):
        results = []
        for key, value in source_dict.items():
            if current.lower() in key.lower():
                label = (
                    label_fn(key, value)
                    if label_fn
                    else key
                )
                results.append(
                    app_commands.Choice(name=label, value=key)
                )
        return results[:25]
    return _autocomplete

async def title_autocomplete(interaction, current: str):
    player = quest_manager.get_or_create_player(interaction.user.id)

    choices = []
    for badge_id in player.badges:
        badge = BADGES.get(badge_id)
        if not badge:
            continue

        title = badge["name"]
        if current.lower() in title.lower():
            choices.append(
                app_commands.Choice(name=title, value=title)
            )

    return choices[:25]

badge_autocomplete = dict_autocomplete(
    BADGES,
    lambda k, v: f"{k} — {v['name']}"
)

async def handle_progression_announcements(guild, member, result):
    channel = guild.get_channel(BADGE_ANNOUNCE_CHANNEL_ID)
    if not channel:
        return

    trinity = quest_manager.get_npc("trinity")
    if not trinity:
        return

    # 🏅 Badge announcement
    if result.get("new_badges"):
        embed = discord.Embed(
            description=(
                f"🏅 **{member.display_name}** has earned a new guild badge!\n\n"
                + "\n".join(
                    f"{BADGES[b]['emoji']} **{BADGES[b]['name']}**"
                    for b in result["new_badges"]
                    if b in BADGES
                )
            ),
            color=discord.Color.gold(),
        )
        embed.set_author(name=trinity.name, icon_url=trinity.avatar_url)
        await channel.send(embed=embed)

    # 🌟 Level-up announcement
    if result.get("level_up"):
        embed = discord.Embed(
            description=(
                f"🌟 **{member.display_name}** has reached "
                f"**Level {result['level_up']}**!"
            ),
            color=discord.Color.blurple(),
        )
        embed.set_author(name=trinity.name, icon_url=trinity.avatar_url)
        await channel.send(embed=embed)

def detect_tavern_intent(text: str) -> str:
    if not text:
        return "base"

    text = text.lower().strip()

    # 🪪 Introduction detection (HIGH PRIORITY)
    introduction_markers = [
        "who are you",
        "who're you",
        "who is grimbald",
        "what's your name",
        "what is your name",
        "introduce yourself",
        "your name",
    ]
    if any(marker in text for marker in introduction_markers):
        return "introduction"

    # 👋 Greeting detection (NEW)
    greetings = [
        "hey", "hi", "hello", "hail", "evening", "evenin",
        "good evening", "good day", "greetings", "morning", "good morning"
    ]
    if any(text == g or text.startswith(g + " ") for g in greetings):
        return "greeting"

    # Second-person questions about Grimbald → deflection
    second_person_markers = [
        "are you",
        "do you",
        "you are",
        "you're",
    ]
    if any(marker in text for marker in second_person_markers):
        return "unknown"
    
    thanks_markers = [
        "thanks", "thank you", "cheers", "much obliged", "appreciate it"
    ]
    if any(marker in text for marker in thanks_markers):
        return "thanks"

    intents = {
        "drink": ["drink", "ale", "beer", "mead", "thirsty"],
        "word": ["word", "rumor", "rumours", "gossip", "heard", "news", "talk"],
        "work": ["work", "job", "quest", "help", "hiring"],
        "food": ["food","eat","eating","meal","meals","dinner","lunch","breakfast","stew","soup","bread","cheese","meat","snack","snacks","grub","rations","hungry","starving","famished"]
    }

    for intent, keywords in intents.items():
        if any(k in text for k in keywords):
            return intent

    # If text exists but no intent matched
    return "unknown"

def pick_tavern_response(npc, intent: str) -> str:
    if intent in ("base", "greeting"):
        return random.choice(npc.greetings)

    if intent == "introduction":
        pool = npc.quest_dialogue.get("INTRODUCTION", [])
        if pool:
            return random.choice(pool)
        return random.choice(npc.greetings)
    
    if intent == "thanks":
        pool = npc.quest_dialogue.get("THANKS", [])
        if pool:
            return random.choice(pool)
        return random.choice(npc.greetings)

    if intent == "unknown":
        pool = npc.quest_dialogue.get("UNKNOWN", [])
        if pool:
            return random.choice(pool)
        return random.choice(npc.greetings)

    pool = npc.quest_dialogue.get(intent.upper(), [])
    if pool:
        return random.choice(pool)

    return npc.default_reply

def mentions_grimbald(message: discord.Message) -> bool:
    return any(role.id == GRIMBALD_ROLE_ID for role in message.role_mentions)

async def get_npc_webhook(channel: discord.TextChannel, npc_name: str) -> discord.Webhook:
    # Return cached webhook if exists
    if channel.id in npc_webhook_cache:
        return npc_webhook_cache[channel.id]

    webhooks = await channel.webhooks()
    for hook in webhooks:
        if hook.name == f"NPC-{npc_name}":
            npc_webhook_cache[channel.id] = hook
            return hook

    # Create new webhook if none found
    hook = await channel.create_webhook(name=f"NPC-{npc_name}")
    npc_webhook_cache[channel.id] = hook
    return hook

async def send_as_npc(
    channel: discord.TextChannel,
    npc,
    content: str
):
    webhook = await get_npc_webhook(channel, npc.name)

    await webhook.send(
        content,
        username=npc.name,
        avatar_url=npc.avatar_url,
        allowed_mentions=discord.AllowedMentions.none()
    )

def strip_grimbald_mention(message: discord.Message) -> str:
    content = message.content

    for role in message.role_mentions:
        if role.id == GRIMBALD_ROLE_ID:
            content = content.replace(f"<@&{role.id}>", "")

    return content.strip()

wandering_manager.refresh_board_callback = refresh_quest_board


# ========= ADMIN: Seasonal and Events =========


@bot.tree.command(name="season_reset",description="Safely reset the seasonal boss state (no file deletion).")
@app_commands.default_permissions(manage_guild=True)
async def season_reset(interaction: discord.Interaction):
    state = get_season_state()

    reset_season_state(state)
    save_season(state)

    await interaction.response.send_message(
        "♻️ **Seasonal state reset safely.**\n"
        "Boss, votes, faction HP, and power usage have been reset.\n"
        "_No data files were deleted._",
        ephemeral=True,
    )


@bot.tree.command(
    name="season_resolve_now",
    description="Force-resolve the seasonal boss for the current day."
)
@app_commands.default_permissions(manage_guild=True)
async def season_resolve_now(interaction: discord.Interaction):
    state = get_season_state()

    if not state.get("active"):
        return await interaction.response.send_message(
            "❌ No active seasonal boss.",
            ephemeral=True,
        )

    # 🔥 Resolve immediately
    summary = resolve_daily_boss(state)

    # 🔄 FORCE reset votes (important)
    reset_votes_for_new_day(state, force=True)

    # 💾 Save
    save_season(state)

    # 🖼️ EDIT the existing seasonal embed
    await update_seasonal_embed(bot)

    # ✅ Admin confirmation only (no new embed)
    await interaction.response.send_message(
        f"⚙️ **Season manually resolved.**\n"
        f"Boss HP: {summary['boss_hp_before']} → {summary['boss_hp_after']}",
        ephemeral=True,
    )


@bot.tree.command(name="season_event", description="Post or refresh the seasonal event.")
@app_commands.default_permissions(manage_guild=True)
async def season_event(interaction: discord.Interaction):
    state = get_season_state()

    embed = build_seasonal_embed()
    view = SeasonalVoteView()

    # If we already have a message, edit it
    if state["embed"]["channel_id"] and state["embed"]["message_id"]:
        try:
            channel = interaction.client.get_channel(state["embed"]["channel_id"])
            if channel is None:
                channel = await interaction.client.fetch_channel(state["embed"]["channel_id"])

            msg = await channel.fetch_message(state["embed"]["message_id"])
            await msg.edit(embed=embed, view=view)

            return await interaction.response.send_message(
                "🔄 Seasonal event updated.",
                ephemeral=True,
            )
        except Exception:
            pass  # Fall through to repost

    # Otherwise post new
    await interaction.response.send_message(embed=embed, view=view)
    msg = await interaction.original_response()

    state["embed"]["channel_id"] = msg.channel.id
    state["embed"]["message_id"] = msg.id
    from systems.seasonal.storage import save_season
    save_season(state)

@bot.tree.command(name="season_faction_adjust",description="Adjust a faction's HP (boss strike or sudden aid).")
@app_commands.default_permissions(manage_guild=True)
@app_commands.choices(
    mode=[
        app_commands.Choice(name="Add (Heal)", value="add"),
        app_commands.Choice(name="Reduce (Damage)", value="reduce"),
    ],
    faction=[
        app_commands.Choice(name="Shieldborne", value="shieldborne"),
        app_commands.Choice(name="Spellfire", value="spellfire"),
        app_commands.Choice(name="Verdant", value="verdant"),
    ],
)
async def season_faction_adjust(
    interaction: discord.Interaction,
    faction: app_commands.Choice[str],
    amount: int,
    mode: app_commands.Choice[str],
    reason: str | None = None,
):
    state = get_season_state()

    if not state.get("active"):
        return await interaction.response.send_message(
            "❌ No active seasonal boss.",
            ephemeral=True,
        )

    fh = state.get("faction_health", {}).get(faction.value)
    boss_name = state.get("boss", {}).get("name", "The Boss")

    if not fh:
        return await interaction.response.send_message(
            "❌ Invalid faction.",
            ephemeral=True,
        )

    old_hp = fh["hp"]
    max_hp = fh["max_hp"]

    if mode.value == "add":
        fh["hp"] = min(max_hp, fh["hp"] + amount)
        delta = fh["hp"] - old_hp
        title = "✨ Sudden Aid!"
        description = (
            f"**{boss_name}** hesitates as restorative forces surge.\n\n"
            f"💚 **{faction.name}** recovers **{delta} HP**."
        )
        color = discord.Color.green()

    else:  # reduce
        fh["hp"] = max(0, fh["hp"] - amount)
        delta = old_hp - fh["hp"]
        title = "💥 Devastating Blow!"
        description = (
            f"**{boss_name}** unleashes a brutal strike!\n\n"
            f"🩸 **{faction.name}** suffers **{delta} damage**."
        )
        color = discord.Color.red()

    if reason:
        description += f"\n\n*{reason}*"

    save_season(state)

    # Update the main seasonal embed
    await update_seasonal_embed(bot)

    # Post narrative embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
    )

    await interaction.channel.send(embed=embed)

    await interaction.response.send_message(
        f"✅ {mode.name} applied to {faction.name}.",
        ephemeral=True,
    )


@bot.tree.command(name="season_boss_set",description="Admin: Edit the seasonal boss (name, HP, phase, avatar).")
@app_commands.default_permissions(manage_guild=True)
async def season_boss_set(
    interaction: discord.Interaction,
    name: str | None = None,
    hp: int | None = None,
    max_hp: int | None = None,
    phase: int | None = None,
    avatar_url: str | None = None,
):
    if not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message(
            "❌ No permission.",
            ephemeral=True,
        )

    state = get_season_state()
    # 🔄 Sync faction power unlocks from quest board
    board = quest_manager.quest_board
    for faction_id, points in board.faction_points.items():
        if (
            points >= board.faction_goal
            and not state["faction_powers"][faction_id]["unlocked"]
        ):
            state["faction_powers"][faction_id]["unlocked"] = True

    boss = state["boss"]

    changes = []

    # ----------------------------------
    # 🆕 START BOSS FIGHT (AUTO BALANCE)
    # ----------------------------------
    starting_new_fight = hp is None and max_hp is None

    if starting_new_fight:
        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ Must be used in a server.",
                ephemeral=True,
            )

        expected_votes = estimate_expected_daily_votes(interaction.guild)
        initialize_season_boss_and_factions(state, expected_votes)

        changes.append(
            f"Boss fight started (auto-balanced for ~7 days, {expected_votes} expected votes/day)"
        )


    if name is not None:
        boss["name"] = name
        changes.append(f"Name → **{name}**")

    if max_hp is not None:
        boss["max_hp"] = max(1, max_hp)
        # Clamp HP if needed
        boss["hp"] = min(boss["hp"], boss["max_hp"])
        changes.append(f"Max HP → **{boss['max_hp']}**")

    if hp is not None:
        boss["hp"] = max(0, min(hp, boss["max_hp"]))
        changes.append(f"HP → **{boss['hp']}**")

    if phase is not None:
        boss["phase"] = max(1, phase)
        changes.append(f"Phase → **{boss['phase']}**")

    if avatar_url is not None:
        boss["avatar_url"] = avatar_url
        changes.append("Avatar updated")

    save_season(state)

    # Update embed if posted
    embed_data = state.get("embed", {})
    if embed_data.get("channel_id") and embed_data.get("message_id"):
        channel = interaction.client.get_channel(embed_data["channel_id"])
        if channel:
            try:
                msg = await channel.fetch_message(embed_data["message_id"])
                await msg.edit(embed=build_seasonal_embed(), view=SeasonalVoteView())
            except Exception:
                pass

    # Log change
    await log_admin_action(
        interaction.client,
        (
            "🐉 **Seasonal Boss Updated**\n"
            f"• Changes:\n" + "\n".join(f"  - {c}" for c in changes) + "\n"
            f"• By: {interaction.user.mention}"
        )
    )

    await interaction.response.send_message(
        "✅ Boss updated successfully.",
        ephemeral=True,
    )

@bot.tree.command(name="quest_admin_spawn_event", description="Admin: Spawn a wandering event in Luneth Vale.")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_spawn_event(
    interaction: discord.Interaction,
    difficulty: Literal["test", "minor", "standard", "major", "critical"],
    title: str,
    description: str,
):
    try:
        await wandering_manager.spawn(
            bot=interaction.client,
            title=title,
            description=description,
            difficulty=difficulty,
        )
        await interaction.response.send_message("✅ Wandering event spawned.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Could not spawn event: {e}", ephemeral=True)



# ========= ADMIN: Badge =========

@bot.tree.command(name="badge_backfill_join_dates",description="Admin: Grant beta/founder badges based on join date.")
@app_commands.default_permissions(manage_guild=True)
async def badge_backfill_join_dates(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    if not guild:
        return

    granted = 0
    scanned = 0

    # 🔥 FORCE FETCH ALL MEMBERS
    async for member in guild.fetch_members(limit=None):
        scanned += 1

        player = quest_manager.get_or_create_player(member.id)
        new_badges = evaluate_join_date_badges(member, player)

        if new_badges:
            granted += len(new_badges)

    quest_manager.save_players()

    await interaction.followup.send(
        f"🧪 Backfill complete.\n"
        f"Scanned **{scanned}** members.\n"
        f"Granted **{granted}** badges.",
        ephemeral=True,
    )

@bot.tree.command(name="badge_grant", description="Admin: Grant a badge to a user.")
@app_commands.autocomplete(badge_id=badge_autocomplete)
@app_commands.default_permissions(manage_guild=True)
async def badge_grant(
    interaction: discord.Interaction,
    member: discord.Member,
    badge_id: str,
):
    if not require_admin(interaction):
        return await interaction.response.send_message(
            "❌ You do not have permission to do this.",
            ephemeral=True,
        )

    player = quest_manager.get_or_create_player(member.id)

    if badge_id in player.badges:
        return await interaction.response.send_message(
            f"ℹ️ **{member.display_name}** already has the badge `{badge_id}`.",
            ephemeral=True,
        )

    player.badges.add(badge_id)
    quest_manager.save_players()

    badge = BADGES.get(badge_id)
    badge_name = badge["name"] if badge else badge_id

    await interaction.response.send_message(
        f"🏅 Granted **{badge_name}** to **{member.display_name}**.",
        ephemeral=True,
    )

@bot.tree.command(name="badge_revoke", description="Admin: Revoke a badge from a user.")
@app_commands.autocomplete(badge_id=badge_autocomplete)
@app_commands.default_permissions(manage_guild=True)
async def badge_revoke(
    interaction: discord.Interaction,
    member: discord.Member,
    badge_id: str,
):
    if not require_admin(interaction):
        return await interaction.response.send_message(
            "❌ You do not have permission to do this.",
            ephemeral=True,
        )

    player = quest_manager.get_or_create_player(member.id)

    if badge_id not in player.badges:
        return await interaction.response.send_message(
            f"ℹ️ **{member.display_name}** does not have the badge `{badge_id}`.",
            ephemeral=True,
        )

    player.badges.discard(badge_id)
    quest_manager.save_players()

    badge = BADGES.get(badge_id)
    badge_name = badge["name"] if badge else badge_id

    await interaction.response.send_message(
        f"🗑️ Revoked **{badge_name}** from **{member.display_name}**.",
        ephemeral=True,
    )

@bot.tree.command(name="badge_grant_all",description="Admin: Grant a badge to all guild players.")
@app_commands.default_permissions(manage_guild=True)
async def badge_grant_all(
    interaction: discord.Interaction,
    badge_id: str,
):
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    count = 0
    for player in quest_manager.players.values():
        if badge_id not in player.badges:
            player.badges.add(badge_id)
            count += 1

    quest_manager.save_players()

    await interaction.response.send_message(
        f"🏅 Granted badge `{badge_id}` to **{count}** players.",
        ephemeral=True,
    )

@bot.tree.command(name="badge_grant_role",description="Admin: Grant a badge to all users with a role.")
@app_commands.default_permissions(manage_guild=True)
async def badge_grant_role(
    interaction: discord.Interaction,
    role: discord.Role,
    badge_id: str,
):
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    count = 0
    for member in role.members:
        player = quest_manager.get_or_create_player(member.id)
        if badge_id not in player.badges:
            player.badges.add(badge_id)
            count += 1

    quest_manager.save_players()

    await interaction.response.send_message(
        f"🏅 Granted badge `{badge_id}` to **{count}** members with role {role.mention}.",
        ephemeral=True,
    )


# ========= ADMIN: Maintenance =========

@bot.tree.command(name="quest_admin_wipe_user", description="Admin: Reset a user's quest profile completely.")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_reset_user(
    interaction: discord.Interaction,
    member: discord.Member,
):
    
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    user_id = member.id

    if user_id not in quest_manager.players:
        await interaction.response.send_message(
            f"ℹ️ {member.display_name} has no guild profile to reset.",
            ephemeral=True,
        )
        return

    del quest_manager.players[user_id]
    quest_manager.save_players()

    await interaction.response.send_message(
        f"🧹 Profile reset for **{member.display_name}** "
        f"(ID: {user_id}). They can start fresh with `/quest`."
    )

@bot.tree.command(name="quest_admin_reset_daily",description="ADMIN: Reset a user's daily quest (keeps profile intact).")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_reset_daily(
    interaction: discord.Interaction,
    member: discord.Member
):
    if not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    player = quest_manager.get_player(member.id)

    if not player:
        return await interaction.response.send_message(
            "⚠️ That user does not have a quest profile.",
            ephemeral=True
        )

    # Only reset the daily quest
    player.daily_quest = {}
    storage.save_players(quest_manager.players)

    await interaction.response.send_message(
        f"🟢 Daily quest reset for **{member.display_name}**.\n"
        "Their profile, XP, and stats were not affected.",
        ephemeral=True
    )

@bot.tree.command(name="quest_admin_cleanup", description="Admin: remove quest profiles for users no longer in the server.")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_cleanup(interaction: discord.Interaction):
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)


    guild = interaction.guild
    valid_ids = {member.id for member in guild.members}

    removed = 0
    for uid in list(quest_manager.players.keys()):
        if uid not in valid_ids:
            del quest_manager.players[uid]
            removed += 1

    quest_manager.save_players()

    await interaction.response.send_message(
        f"🧹 Cleaned up **{removed}** profiles no longer in the server."
    )

@bot.tree.command(name="ping", description="Test that the bot is alive.")
@app_commands.default_permissions(manage_guild=True)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🦊 Pong!", ephemeral=True)



# ========= ADMIN: Import / Export =========

@bot.tree.command(name="quest_import",description="ADMIN: Import Quest JSON file (overwrite or merge).")
@app_commands.default_permissions(manage_guild=True)
async def quest_import(interaction: discord.Interaction, file: discord.Attachment, mode: str = "overwrite"):
    if not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    if mode not in ("overwrite", "merge"):
        return await interaction.response.send_message("❌ Mode must be overwrite or merge.", ephemeral=True)

    try:
        raw_bytes = await file.read()
        new_data = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        return await interaction.response.send_message(f"❌ JSON error: {e}", ephemeral=True)
        
    valid, msg = validate_quest_data(new_data)
    if not valid:
        return await interaction.response.send_message(f"❌ Import failed: {msg}", ephemeral=True)
    
    # Load existing quests.json
    try:
        with open(QUESTS_FILE, "r", encoding="utf-8") as f:
            current = json.load(f)
    except:
        current = {}

    final_data = new_data if mode == "overwrite" else {**current, **new_data}

    # Save updated quests.json
    with open(QUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4)

    # Reload templates into memory
    quest_manager.reload_templates()

    await interaction.response.send_message(
        f"🟢 Quest import complete! Mode: **{mode}**\nImported **{len(new_data)}** quest(s).",
        ephemeral=True
    )

@bot.tree.command(name="quest_export",description="ADMIN: Export current quest JSON file.")
@app_commands.default_permissions(manage_guild=True)
async def quest_export(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)


    # Load the raw quests.json file exactly as-is
    try:
        with open(QUESTS_FILE, "r", encoding="utf-8") as f:
            quests = json.load(f)
    except Exception as e:
        return await interaction.response.send_message(
            f"❌ Error reading quests.json: {e}",
            ephemeral=True
        )

    content = json.dumps(quests, indent=4)

    buffer = io.BytesIO(content.encode("utf-8"))

    file = discord.File(
        fp=buffer,
        filename="quests_export.json"
    )

    await interaction.response.send_message(
        content="📦 Quest export file:",
        file=file,
        ephemeral=True
    )

@bot.tree.command(name="quest_admin_list_quests",description="Admin: List all quest templates.")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_list_quests(interaction: discord.Interaction):
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)


    if not quest_manager.quest_templates:
        await interaction.response.send_message(
            "ℹ️ No quest templates are currently defined.",
            ephemeral=True,
        )
        return

    lines: list[str] = []
    for qid, tmpl in sorted(quest_manager.quest_templates.items()):
        roles = getattr(tmpl, "allowed_roles", []) or []
        role_str = ", ".join(f"<@&{rid}>" for rid in roles) if roles else "Everyone"
        lines.append(
            f"- `{qid}` — **{tmpl.name}** ({tmpl.type.value}, {tmpl.points} pts) "
            f"[Roles: {role_str}]"
        )

    msg = "**Current Quest Templates:**\n" + "\n".join(lines)
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="npc_import",description="ADMIN: Import NPC JSON file (overwrite or merge).")
@app_commands.default_permissions(manage_guild=True)
async def npc_import(
    interaction: discord.Interaction,
    file: discord.Attachment,
    mode: str = "overwrite"
):
    if not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    if mode not in ("overwrite", "merge"):
        return await interaction.response.send_message("❌ Mode must be 'overwrite' or 'merge'.", ephemeral=True)

    # Read uploaded JSON
    try:
        raw_bytes = await file.read()
        new_data = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        return await interaction.response.send_message(f"❌ JSON error: {e}", ephemeral=True)
    
    valid, msg = validate_npc_data(new_data)
    if not valid:
        return await interaction.response.send_message(f"❌ Import failed: {msg}", ephemeral=True)
        
    # Load existing NPCs
    current = storage.load_npcs()

    # Overwrite or merge
    if mode == "overwrite":
        final_data = new_data
    else:  # merge
        final_data = {**current, **new_data}

    # Save final NPC JSON
    storage.save_npcs(final_data)
    quest_manager.reload_npcs()


    await interaction.response.send_message(
        f"🟢 NPC import complete! Mode: **{mode}**\n"
        f"Imported **{len(new_data)}** NPC(s).",
        ephemeral=True
    )

@bot.tree.command(name="npc_export",description="ADMIN: Export current NPC JSON file.")
@app_commands.default_permissions(manage_guild=True)
async def npc_export(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    npcs = storage.load_npcs()
    serializable = {npc_id: npc.to_dict() for npc_id, npc in npcs.items()}
    content = json.dumps(serializable, indent=4)

    buffer = io.BytesIO(content.encode("utf-8"))

    file = discord.File(
        fp=buffer,
        filename="npcs_export.json"
    )


    await interaction.response.send_message(
        content="📦 NPC export file:",
        file=file,
        ephemeral=True
    )

@bot.tree.command(name="quest_admin_list_npcs",description="Admin: List all quest NPCs.")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_list_npcs(interaction: discord.Interaction):
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    if not quest_manager.npcs:
        await interaction.response.send_message(
            "ℹ️ No NPCs are currently defined.",
            ephemeral=True,
        )
        return

    lines: list[str] = []
    for npc_id, npc in sorted(quest_manager.npcs.items()):
        lines.append(f"- `{npc_id}` — **{npc.name}**")

    msg = "**Current Quest NPCs:**\n" + "\n".join(lines)
    await interaction.response.send_message(msg, ephemeral=True)
 


# ========= ADMIN: Board =========

@bot.tree.command(name="quest_board",description="Show or update the Jolly Fox seasonal quest scoreboard.")
@app_commands.default_permissions(manage_guild=True)
async def quest_board_cmd(interaction: discord.Interaction):
    board = quest_manager.quest_board
    embed = build_board_embed()

    # Attempt to update existing board
    if board.display_channel_id and board.message_id:
        try:
            channel = interaction.client.get_channel(board.display_channel_id)
            if channel is None:
                channel = await interaction.client.fetch_channel(
                    board.display_channel_id
                )

            msg = await channel.fetch_message(board.message_id)
            await msg.edit(embed=embed, view=QuestBoardView())

            await interaction.response.send_message(
                "🔄 Quest board updated.",
                ephemeral=True,
            )
            return

        except Exception as e:
            print("Quest board update failed:", e)
            await interaction.response.send_message(
                "⚠️ Failed to update the existing quest board.\n"
                "Use `/quest_admin_reset_board` and rerun `/quest_board`.",
                ephemeral=True,
            )
            return

    # ✅ NO BOARD EXISTS → POST IT
    await interaction.response.send_message(
        embed=embed,
        view=QuestBoardView()
    )

    msg = await interaction.original_response()
    board.display_channel_id = msg.channel.id
    board.message_id = msg.id
    quest_manager.save_board()


@bot.tree.command(name="quest_admin_set_season",description="Admin: Start a new season and set goal/reward text.")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_set_season(
    interaction: discord.Interaction,
    season_id: str,
    season_goal: int,
    faction_goal: int,
    season_reward: str | None = None,
):
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    board = quest_manager.quest_board
    board.reset_season(season_id)
    board.season_goal = max(1, season_goal)
    board.faction_goal = max(1, faction_goal)
    board.season_reward = season_reward or ""

    quest_manager.save_board()
    await refresh_quest_board(interaction.client)

    await log_admin_action(
        interaction.client,
        (
            f"📅 **Season Started / Reset**\n"
            f"• Season ID: **{season_id}**\n"
            f"• Guild Goal: **{board.season_goal}** points\n"
            f"• Faction Power Goal: **{board.faction_goal}** points\n"
            f"• Reward: {board.season_reward or 'None'}\n"
            f"• By: {interaction.user.mention}"
        )
    )

    await interaction.response.send_message(
        f"✅ Season set to **{season_id}** with goal **{board.season_goal}** points.",
        ephemeral=True,
        
    )

@bot.tree.command(name="quest_admin_set_board_meta",description="Admin: Edit the seasonal goal or reward text without resetting points.")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_set_board_meta(
    interaction: discord.Interaction,
    season_goal: int | None = None,
    faction_goal: int | None = None,
    season_reward: str | None = None,
):
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    if season_goal is None and faction_goal is None and season_reward is None:
        await interaction.response.send_message(
            "⚠️ You must provide at least one of `season_goal` or `season_reward`.",
            ephemeral=True,
        )
        return

    board = quest_manager.quest_board

    if season_goal is not None:
        board.season_goal = max(1, season_goal)
    if season_reward is not None:
        board.season_reward = season_reward
    if faction_goal is not None:
        board.faction_goal = max(1, faction_goal)

    quest_manager.save_board()
    await refresh_quest_board(interaction.client)

    log_lines = ["📝 **Season Metadata Updated**"]

    if season_goal is not None:
        log_lines.append(f"• New Goal: **{board.season_goal}** points")

    if season_reward is not None:
        log_lines.append(f"• New Reward: {board.season_reward}")
    
    if faction_goal is not None:
        log_lines.append(f"• New Faction Power Goal: **{board.faction_goal}** points")

    log_lines.append(f"• By: {interaction.user.mention}")

    await log_admin_action(
        interaction.client,
        "\n".join(log_lines)
    )


    await interaction.response.send_message(
        "✅ Quest board metadata updated.",
        ephemeral=True,
    )

@bot.tree.command(name="quest_admin_reset_board",description="Admin: Reset the current season and force board recreation.")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_reset_board(interaction: discord.Interaction):
    if not require_admin(interaction):
        return await interaction.response.send_message(
            "❌ No permission.",
            ephemeral=True,
        )

    board = quest_manager.quest_board

    # 🔥 CLEAR BOARD ANCHOR (THIS IS THE HEAL)
    board.display_channel_id = None
    board.message_id = None

    # 🔄 RESET BOARD STATE
    board.global_points = 0
    board.faction_points = {}

    # 🔄 RESET PLAYER SEASONAL STATS
    for player in quest_manager.players.values():
        player.season_completed = 0
        player.monsters_season = 0

    quest_manager.save_players()
    quest_manager.save_board()

    await interaction.response.send_message(
        "🧹 **Season reset complete.**\n"
        "The quest board will be recreated the next time `/quest_board` is run.",
        ephemeral=True,
    )

@bot.tree.command(name="quest_admin_adjust_points",description="Admin: Adjust faction or global guild points (add or remove).")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_adjust_points(
    interaction: discord.Interaction,
    points: int,
    faction: str | None = None,
    reason: str | None = None,
):
    if not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message(
            "❌ No permission.",
            ephemeral=True,
        )

    board = quest_manager.quest_board
    actor = interaction.user.mention

    # 🔹 Determine target
    if faction:
        faction = faction.lower()
        if faction not in FACTIONS:
            return await interaction.response.send_message(
                f"❌ Invalid faction. Valid options: {', '.join(FACTIONS.keys())}",
                ephemeral=True,
            )

        board.faction_points[faction] = board.faction_points.get(faction, 0) + points
        board.global_points += points
        target_name = FACTIONS[faction].name
        target_text = f"Faction: **{target_name}**"

    else:
        board.global_points += points
        target_text = "**Global Guild Total**"

    quest_manager.save_board()
    await refresh_quest_board(interaction.client)

    # 🧾 Build log message
    log_msg = (
        f"🛠️ **Guild Point Adjustment**\n"
        f"• Target: {target_text}\n"
        f"• Points: **{points:+}**\n"
        f"• By: {actor}\n"
        f"{f'• Reason: {reason}' if reason else ''}"
    )

    # 📢 Send to log channel
    log_channel = interaction.client.get_channel(POINTS_LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(log_msg)

    # 🔒 Confirm to admin
    await interaction.response.send_message(
        "✅ Points adjusted and logged.",
        ephemeral=True,
    )



# ========= PLAYER: Core =========

@bot.tree.command(name="quest",description="See your daily Jolly Fox guild quest.")
async def quest(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await send_daily_quest(interaction)

@bot.tree.command(name="profile")
async def profile(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)

    player = quest_manager.get_or_create_player(interaction.user.id)
    embed = build_profile_embed(
        viewer=interaction.user,
        target=interaction.user,
        player=player,
    )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="profile_user",description="View another guild member’s profile.")
async def profile_user(interaction: discord.Interaction,member: discord.Member,):
    await interaction.response.defer(ephemeral=False)

    player = quest_manager.get_or_create_player(member.id)
    embed = build_profile_embed(
        viewer=interaction.user,
        target=member,
        player=player,
    )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="title_set", description="Set your active guild title.")
@app_commands.autocomplete(title=title_autocomplete)
async def title_set(
    interaction: discord.Interaction,
    title: str,
):
    player = quest_manager.get_or_create_player(interaction.user.id)

    # Safety: make sure they still own it
    valid_titles = {
        BADGES[b]["name"]
        for b in player.badges
        if b in BADGES
    }

    if title not in valid_titles:
        return await interaction.response.send_message(
            "❌ You don’t have that title unlocked.",
            ephemeral=True,
        )

    player.title = title
    quest_manager.save_players()

    await interaction.response.send_message(
        f"🎖️ Your title is now **{title}**.",
        ephemeral=True,
    )


# ========= PLAYER: Quest Actions =========

@bot.tree.command(name="talk",description="Speak with the required NPC to complete your quest.")
async def talk(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    # Validate daily quest + ensure type = SOCIAL
    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.SOCIAL
    )
    if player is None:
        return

    # Enforce required channel
    required_channel = template.required_channel_id
    if required_channel and interaction.channel_id != required_channel:
        return await interaction.followup.send(
            f"❌ You must speak with **{template.npc_id}** in <#{required_channel}>.",
            ephemeral=True,
        )

    npc = quest_manager.get_npc(template.npc_id)
    if npc is None:
        return await interaction.followup.send(
            f"⚠️ Error: NPC `{template.npc_id}` not found.",
            ephemeral=True,
        )

    # -------------------------------------------------------------
    # NPC DIALOGUE SELECTION LOGIC
    # -------------------------------------------------------------
    reply_text = get_npc_quest_dialogue(npc, template)

    result = quest_manager.complete_daily(interaction.user.id)

    if result.get("completed"):
        await handle_progression_announcements(
            interaction.guild,
            interaction.user,
            result,
    )

    faction_id = get_member_faction_id(interaction.user)
    quest_manager.award_points(interaction.user.id, QUEST_POINTS, faction_id)
    await refresh_quest_board(interaction.client)

    # -------------------------------------------------------------
    # Send message
    # -------------------------------------------------------------
    await send_npc_response(
        interaction,
        npc=npc,
        dialogue=reply_text,
        title="Conversation Complete",
        footer=f"✨ **Quest complete!** You earned **{QUEST_POINTS}** guild points.",
    )

@bot.tree.command(name="skill", description="Attempt a SKILL quest roll.")
async def skill(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.SKILL
    )
    if player is None:
        return

    required_channel = template.required_channel_id
    if required_channel and interaction.channel_id != required_channel:
        await interaction.followup.send(
            f"❌ You must attempt this training in <#{required_channel}>.",
            ephemeral=True,
        )
        return

    dc = template.dc or 10
    roll = random.randint(1, 20)
    success = roll >= dc
    result_text = (
        f"🎯 You rolled **{roll}** (DC {dc}) — **Success!**"
        if success else
        f"💥 You rolled **{roll}** (DC {dc}) — **You fall short.**"
    )

    # 📜 Get NPC dialogue FIRST
    npc = quest_manager.get_npc(template.npc_id) if template.npc_id else None
    dialogue = (
        get_npc_quest_dialogue(npc, template, success=success)
        if npc
        else None
    )
    result = quest_manager.complete_daily(interaction.user.id)

    if result.get("completed"):
        await handle_progression_announcements(
            interaction.guild,
            interaction.user,
            result,
    )

        faction_id = get_member_faction_id(interaction.user)
        quest_manager.award_points(interaction.user.id,QUEST_POINTS,faction_id)
        await refresh_quest_board(interaction.client)

    # 🎭 NPC = embed | ⚙️ No NPC = text
    if npc:
        await send_npc_response(
            interaction,
            npc=npc,
            dialogue=dialogue or "The training concludes.",
            title="Training Complete",
            footer=(
                f"{result_text}\n\n✨ You earned **{QUEST_POINTS}** guild points."
            )
        )
    else:
        await interaction.followup.send(
            (
                f"🎯 **Training Complete**\n\n"
                f"{result_text}\n\n"
                f"✨ You earned **{QUEST_POINTS}** guild points."
            ),
            ephemeral=True
        )

@bot.tree.command(name="checkin", description="Complete a TRAVEL quest by checking in at the right location.")
async def checkin(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.TRAVEL
    )
    if player is None:
        return

    required_channel = template.required_channel_id or 0
    if required_channel and interaction.channel_id != required_channel:
        await interaction.followup.send(
            f"❌ You must check in at <#{required_channel}> for this quest.",
            ephemeral=True,
        )
        return

    npc = quest_manager.get_npc(template.npc_id) if template.npc_id else None
    dialogue = get_npc_quest_dialogue(npc, template) if npc else None
    result = quest_manager.complete_daily(interaction.user.id)

    if result.get("completed"):
        await handle_progression_announcements(
            interaction.guild,
            interaction.user,
            result,
    )
        
    faction_id = get_member_faction_id(interaction.user)
    quest_manager.award_points(interaction.user.id, QUEST_POINTS, faction_id)
    await refresh_quest_board(interaction.client)

    await send_npc_response(
    interaction,
    npc=npc,
    dialogue=dialogue or "You check in at your destination.",
    title="Arrival Confirmed",
    footer=f"✨ **Quest complete!** You earned **{QUEST_POINTS}** guild points.",
    )

@bot.tree.command(name="fetch", description="Collect the required item for a FETCH quest.")
async def fetch(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.FETCH
    )
    if player is None:
        return

    source_channel = template.source_channel_id or 0
    if source_channel and interaction.channel_id != source_channel:
        await interaction.followup.send(
            f"❌ You can only gather this in <#{source_channel}>.",
            ephemeral=True,
        )
        return

    # ✅ DEFINE EARLY (FIX)
    turnin_channel = template.turnin_channel_id or 0

    # 🔒 Already have item
    if player.has_item_for_quest(template.item_name):
        turnin_hint = (
            f"<#{turnin_channel}> and use `/turnin`"
            if turnin_channel
            else "`/turnin` in the guild office channel"
        )

        await interaction.followup.send(
            "📦 You've already gathered this quest item.\n"
            f"Head to {turnin_hint}.",
            ephemeral=True,
        )
        return

    # 📦 Collect item
    item_name = template.item_name or "Quest Item"
    player.add_item(item_name)
    quest_manager.save_players()

    turnin_hint = (
        f"<#{turnin_channel}> with `/turnin`"
        if turnin_channel
        else "`/turnin` in the guild office channel"
    )

    await interaction.followup.send(
    f"📦 You gather **{item_name}**.\n\n"
    f"Now take it to {turnin_hint} to complete your quest.",
    ephemeral=True
)

@bot.tree.command(name="turnin", description="Turn in the collected item for your FETCH quest.")
async def turnin(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.FETCH
    )
    if player is None:
        return

    turnin_channel = template.turnin_channel_id or 0
    if turnin_channel and interaction.channel_id != turnin_channel:
        await interaction.followup.send(
            f"❌ You must turn this in at <#{turnin_channel}>.",
            ephemeral=True,
        )
        return

    if not player.has_item_for_quest(template.item_name):
        await interaction.followup.send(
            "❌ You don't have the required quest item yet. "
            "Use `/fetch` in the correct channel first.",
            ephemeral=True,
        )
        return

    # 📜 Get NPC dialogue FIRST (while quest is still active)
    npc = quest_manager.get_npc(template.npc_id) if template.npc_id else None

    if npc:
        dialogue = get_npc_quest_dialogue(npc, template)

        # 🛠 FETCH quests should ALWAYS feel acknowledged
        if not dialogue and template.type == QuestType.FETCH:
            dialogue = "Oh thank you—this really helps!"
    else:
        dialogue = None


    npc_name = npc.name if npc else "The Guild"
    reply = (
        dialogue
        if dialogue
        else f"You turn in **{template.item_name}** to the guild."
    )

    # 📦 Consume item
    player.consume_item(template.item_name)
    quest_manager.save_players()
    result = quest_manager.complete_daily(interaction.user.id)

    if result.get("completed"):
        await handle_progression_announcements(
            interaction.guild,
            interaction.user,
            result,
    )
    faction_id = get_member_faction_id(interaction.user)
    quest_manager.award_points(interaction.user.id, QUEST_POINTS, faction_id)
    await refresh_quest_board(interaction.client)

    await send_npc_response(
    interaction,
    npc=npc,
    dialogue=reply,
    title="Quest Turn-In",
    footer=f"✨ **Quest complete!** You earned **{QUEST_POINTS}** guild points.",)



# ========= Events =========

# # CLEAR COMMANDS ONE TIME. UNCOMMENT, DEPLOY, RECOMMENT, REDEPLOY
# @bot.event
# async def on_ready():
#     print(f"Logged in as {bot.user}")

#     # 🔴 WIPE GLOBAL COMMANDS
#     bot.tree.clear_commands()
#     await bot.tree.sync()

#     print("⚠ Global commands wiped and resynced")


@bot.event
async def setup_hook():
    guild = discord.Object(id=GUILD_ID)

    # Copy all global commands into the guild
    bot.tree.copy_global_to(guild=guild)

async def sleep_until_midnight_utc():
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    await asyncio.sleep((tomorrow - now).total_seconds())


@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    cmds = await bot.tree.sync(guild=guild)
    print(f"Synced {len(cmds)} commands to guild {GUILD_ID}")
    print(f"Logged in as {bot.user}")

    # Sync commands (you already do this)
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    await wandering_manager.startup_resume(bot)

    bot.loop.create_task(
        wandering_manager.scheduled_spawn_loop(bot)
    )

    bot.loop.create_task(seasonal_midnight_loop(bot))

    # 🔹 AUTO refresh quest board
    try:
        await refresh_quest_board(bot)
        print("Quest board refreshed on startup.")
    except Exception as e:
        print(f"Quest board refresh failed: {e}")

@bot.event
async def on_member_join(member: discord.Member):
    player = quest_manager.get_or_create_player(member.id)

    new_badges = evaluate_join_date_badges(member, player)
    if new_badges:
        quest_manager.save_players()

        # Optional: public Trinity announcement
        await handle_progression_announcements(
            member.guild,
            member,
            {
                "new_badges": new_badges,
                "level_up": None,
            }
        )

@bot.event
async def on_member_remove(member: discord.Member):
    user_id = member.id
    if quest_manager.clear_player(user_id):
        print(f"[CLEANUP] Removed player data for {member.display_name} ({user_id})")

@bot.event
async def on_message(message: discord.Message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    # Tavern gate
    TAVERN_CHANNEL_ID = int(os.getenv("TAVERN_CHANNEL_ID"))
    if message.channel.id != TAVERN_CHANNEL_ID:
        return

    # Must explicitly ping Grimbald role
    if not mentions_grimbald(message):
        return

    # Remove role mention text
    content = strip_grimbald_mention(message)
    content = content.lower()
    print(f"[DEBUG] Tavern content after strip: '{content}'")

    npc = quest_manager.get_npc("grimbald")
    if not npc:
        return

    intent = detect_tavern_intent(content)
    response = pick_tavern_response(npc, intent)

    if response:
        async with message.channel.typing():
            await send_as_npc(
                message.channel,
                npc,
                response
            )

bot.run(TOKEN)
