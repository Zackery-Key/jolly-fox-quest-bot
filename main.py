import os
import discord
from discord.ext import commands
import random
from systems.quests.quest_models import QuestType

from systems.quests.factions import FACTIONS, get_faction  # you already have this

# --- Faction role mapping (replace with your real IDs) ---
SHIELDBORNE_ROLE_ID = 1447646082459762761  # TODO: put Shieldborne role ID here
SPELLFIRE_ROLE_ID   = 1447646480889548800  # TODO: Spellfire role ID
VERDANT_ROLE_ID     = 1447644562397859921  # TODO: Verdant role ID

FACTION_ROLE_IDS = {
    "shieldborne": SHIELDBORNE_ROLE_ID,
    "spellfire": SPELLFIRE_ROLE_ID,
    "verdant": VERDANT_ROLE_ID,
}


# Quest Manager
from systems.quests.quest_manager import QuestManager
quest_manager = QuestManager()
print("QUEST MANAGER INITIALIZED")

# Env
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))

if not TOKEN or not GUILD_ID:
    raise ValueError("Missing DISCORD_TOKEN or GUILD_ID environment variable.")

# Bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# Register commands for guild scope
@bot.event
async def setup_hook():
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    print(f"Setup complete for guild {GUILD_ID}")

# Helpers
def get_member_faction_id(member: discord.Member) -> str | None:
    """
    Return the faction_id for this member based on their Discord roles.
    If they don't have any faction role, return None.
    """
    member_role_ids = {role.id for role in member.roles}

    for faction_id, role_id in FACTION_ROLE_IDS.items():
        if role_id in member_role_ids:
            return faction_id

    return None

def make_progress_bar(value: int, max_value: int, length: int = 20) -> str:
    """Simple text progress bar for embeds."""
    if max_value <= 0:
        max_value = 1

    ratio = value / max_value
    if ratio < 0:
        ratio = 0
    if ratio > 1:
        ratio = 1

    filled = int(ratio * length)
    empty = length - filled

    return f"[{'█' * filled}{'░' * empty}]"

async def refresh_quest_board(bot):
    """Update the existing quest board message if we have one saved."""
    board = quest_manager.quest_board

    if not board.display_channel_id or not board.message_id:
        return  # No board created yet

    try:
        channel = bot.get_channel(board.display_channel_id)
        if channel is None:
            channel = await bot.fetch_channel(board.display_channel_id)

        msg = await channel.fetch_message(board.message_id)

        # Generate a fresh embed
        stats = quest_manager.get_scoreboard()
        global_points = stats["global_points"]
        lifetime_completed = stats["lifetime_completed"]
        season_completed = stats["season_completed"]

        SEASON_GOAL = 100
        progress_bar = make_progress_bar(global_points, SEASON_GOAL)

        embed = discord.Embed(
            title="🛡️ Jolly Fox Guild Quest Board",
            description="Seasonal progress for the whole guild.",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="📊 Global Guild Points",
            value=f"{global_points} / {SEASON_GOAL} pts\n{progress_bar}",
            inline=False
        )

        embed.add_field(
            name="🏆 Quests Completed This Season",
            value=str(season_completed),
            inline=True
        )

        embed.add_field(
            name="🌟 Lifetime Quests Completed (All Players)",
            value=str(lifetime_completed),
            inline=True
        )

        embed.set_footer(
            text="Every completed quest pushes the Jolly Fox further this season."
        )

        await msg.edit(embed=embed)

    except Exception as e:
        print("⚠ Failed to refresh quest board:", e)

async def _ensure_active_daily(interaction, expected_type=None, create_if_missing=True):
    """
    Shared guard for daily quest commands.
    - Ensures the user has a daily quest.
    - Ensures it is not already completed.
    - Optionally ensures the quest type matches expected_type.
    Returns (player, template) or (None, None) if it handled the error.
    """
    user_id = interaction.user.id

    # Create profile only when appropriate
    if create_if_missing:
        player = quest_manager.get_or_create_player(user_id)
    else:
        player = quest_manager.get_player(user_id)

    # No profile exists AND we are not allowed to create one
    if not player:
        await interaction.response.send_message(
            "You do not have a guild profile yet. Use `/quest_today` to begin.",
            ephemeral=True
        )
        return None, None

    # No daily quest assigned
    if not player.daily_quest:
        await interaction.response.send_message(
            "🦊 You don't have an active quest today. Use `/quest_today` first.",
            ephemeral=True
        )
        return None, None

    # Corrupted data guard
    if "quest_id" not in player.daily_quest:
        await interaction.response.send_message(
            "⚠️ Your daily quest data is incomplete. Use `/quest_today` to refresh.",
            ephemeral=True
        )
        return None, None

    # Already completed
    if player.daily_quest.get("completed"):
        await interaction.response.send_message(
            "✅ You've already completed today's quest.",
            ephemeral=True
        )
        return None, None

    quest_id = player.daily_quest.get("quest_id")
    template = quest_manager.get_template(quest_id)

    # Template missing (data issue)
    if template is None:
        await interaction.response.send_message(
            "⚠️ Error: Your quest template could not be found. Please tell an admin.",
            ephemeral=True
        )
        return None, None

    # Type mismatch
    if expected_type is not None and template.type != expected_type:
        await interaction.response.send_message(
            f"❌ Your current quest is `{template.type.value}`, not `{expected_type.value}`.\n"
            f"Use the correct command for your quest type.",
            ephemeral=True
        )
        return None, None

    return player, template



# Commands
@bot.tree.command(name="quest_board", description="Show or update the Jolly Fox seasonal quest scoreboard.")
async def quest_board(interaction: discord.Interaction):
    stats = quest_manager.get_scoreboard()

    global_points = stats["global_points"]
    lifetime_completed = stats["lifetime_completed"]
    season_completed = stats["season_completed"]

    SEASON_GOAL = 100  # you can tweak this anytime
    progress_bar = make_progress_bar(global_points, SEASON_GOAL)

    embed = discord.Embed(
        title="🛡️ Jolly Fox Guild Quest Board",
        description="Seasonal progress for the whole guild.",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="📊 Global Guild Points",
        value=f"{global_points} / {SEASON_GOAL} pts\n{progress_bar}",
        inline=False
    )

    embed.add_field(
        name="🏆 Quests Completed This Season",
        value=str(season_completed),
        inline=True
    )

    embed.add_field(
        name="🌟 Lifetime Quests Completed (All Players)",
        value=str(lifetime_completed),
        inline=True
    )

    embed.set_footer(
        text="Every completed quest pushes the Jolly Fox further this season."
    )

    board = quest_manager.quest_board
    updated_existing = False

    # Try to edit existing board message if we know where it lives
    if board.display_channel_id and board.message_id:
        channel = interaction.client.get_channel(board.display_channel_id)
        try:
            if channel is None:
                channel = await interaction.client.fetch_channel(board.display_channel_id)

            msg = await channel.fetch_message(board.message_id)
            await msg.edit(embed=embed)
            updated_existing = True
        except Exception:
            # message/channel might have been deleted; fall back to creating a new one
            updated_existing = False

    if not updated_existing:
        # Create a new PUBLIC board message in the current channel
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        board.display_channel_id = msg.channel.id
        board.message_id = msg.id
        quest_manager.save_board()
    else:
        # We updated the existing pinned board; give a quiet thumbs-up
        await interaction.response.send_message(
            "🔄 Updated the existing quest board message.",
            ephemeral=True
        )


@bot.tree.command(name="quest_admin_reset_user", description="Admin: Reset a user's quest profile completely.")
async def quest_admin_reset_user(
    interaction: discord.Interaction,
    member: discord.Member
):
    # Permission check
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True
        )
        return

    user_id = member.id

    # Check if the player exists
    if user_id not in quest_manager.players:
        await interaction.response.send_message(
            f"ℹ️ {member.display_name} has no guild profile to reset.",
            ephemeral=True
        )
        return

    # Delete the player profile
    del quest_manager.players[user_id]
    quest_manager.save_players()

    await interaction.response.send_message(
        f"🧹 Profile reset for **{member.display_name}** "
        f"(ID: {user_id}). They can start fresh with `/quest_today`."
    )


@bot.tree.command(name="quest_admin_cleanup", description="Admin: remove quest profiles for users no longer in the server.")
async def quest_admin_cleanup(interaction: discord.Interaction):

    # Permission check
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True
        )
        return

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
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🦊 Pong!", ephemeral=True)


@bot.tree.command(name="quest_today", description="See your daily Jolly Fox guild quest.")
async def quest_today(interaction: discord.Interaction):
    user_id = interaction.user.id

    # Make sure you have today's quest (won't change if already assigned today)
    quest_id = quest_manager.assign_daily(user_id)
    template = quest_manager.get_template(quest_id)
    player = quest_manager.get_player(user_id)

    if template is None:
        await interaction.response.send_message(
            "⚠️ Error loading your quest. No templates found or quest is invalid.",
            ephemeral=True
        )
        return

    completed = bool(player.daily_quest.get("completed"))

    # Status + header
    status_label = "✅ COMPLETED" if completed else "🟠 ACTIVE"
    qtype_str = template.type.value if hasattr(template.type, "value") else str(template.type)

    header = f"**🦊 Your Daily Quest — {status_label}**\n"
    body = (
        f"**Name:** {template.name}\n"
        f"**Type:** `{qtype_str}`\n\n"
        f"**Summary:** {template.summary}\n"
    )

    hint_lines: list[str] = []

    # --- SOCIAL ---
    if template.type == QuestType.SOCIAL:
        if template.required_channel_id:
            hint_lines.append(
                f"• Go to <#{template.required_channel_id}> and use `/quest_npc`."
            )
        else:
            hint_lines.append("• Use `/quest_npc` in the appropriate RP channel.")
        if template.npc_id:
            hint_lines.append(f"• Required NPC: `{template.npc_id}`")

    # --- SKILL ---
    elif template.type == QuestType.SKILL:
        if template.required_channel_id:
            hint_lines.append(
                f"• Go to <#{template.required_channel_id}> and use `/quest_skill`."
            )
        else:
            hint_lines.append("• Use `/quest_skill` to attempt your training roll.")
        if template.dc:
            hint_lines.append(f"• Target DC: **{template.dc}**")

    # --- TRAVEL ---
    elif template.type == QuestType.TRAVEL:
        if not template.required_channel_id:
            hint_lines.append(
                "⚠️ This TRAVEL quest is misconfigured (no required_channel_id). "
                "Please tell an admin."
            )
        else:
            hint_lines.append(
                f"• Go to <#{template.required_channel_id}> and use `/quest_checkin`."
            )

    # --- FETCH ---
    elif template.type == QuestType.FETCH:
        src = template.source_channel_id
        turnin = template.turnin_channel_id

        if not src or not turnin:
            hint_lines.append(
                "⚠️ This FETCH quest is misconfigured (missing source/turn-in channel). "
                "Please tell an admin."
            )
        else:
            hint_lines.append(
                f"• First, go to <#{src}> and use `/quest_fetch` to gather the item."
            )
            hint_lines.append(
                f"• Then, go to <#{turnin}> and use `/quest_turnin` to complete the quest."
            )

        if template.item_name:
            hint_lines.append(f"• Required item: **{template.item_name}**")

    # --- Fallback for unknown types ---
    else:
        hint_lines.append("• Use the appropriate quest command for this type.")

    # Completed vs not completed footer
    if completed:
        footer = (
            "\n\n✨ You’ve already completed this quest for today. "
            "Come back tomorrow for a new one, or ask an admin to reset your quest if you're testing."
        )
    else:
        footer = "\n\n✨ Complete this quest to earn guild points for today."

    hint_text = ""
    if hint_lines:
        hint_text = "\n\n**How to complete it:**\n" + "\n".join(hint_lines)

    msg = header + "\n" + body + hint_text + footer

    await interaction.response.send_message(msg)


@bot.tree.command(name="quest_npc", description="Speak with the required NPC to complete your quest.")
async def quest_npc(interaction: discord.Interaction):
    # Shared guards: has quest, not completed, type = SOCIAL
    player, template = await _ensure_active_daily(
        interaction,
        expected_type=QuestType.SOCIAL
    )
    if player is None:
        return  # guard already responded

    # Enforce required channel
    required_channel = template.required_channel_id
    if required_channel and interaction.channel_id != required_channel:
        await interaction.response.send_message(
            f"❌ You must speak with **{template.npc_id}** in <#{required_channel}>.",
            ephemeral=True
        )
        return

    # Load NPC
    npc = quest_manager.get_npc(template.npc_id)
    if npc is None:
        await interaction.response.send_message(
            f"⚠️ Error: NPC `{template.npc_id}` not found.",
            ephemeral=True
        )
        return

    quest_manager.complete_daily(interaction.user.id)

    faction_id = get_member_faction_id(interaction.user)
    quest_manager.award_points(interaction.user.id, template.points, faction_id)
    await refresh_quest_board(interaction.client)

    reply_text = npc.default_reply or "They acknowledge your presence."

    await interaction.response.send_message(
        f"**{npc.name}** says:\n> {reply_text}\n\n"
        f"✨ **Quest complete!** You earned **{template.points}** guild points."
    )


@bot.tree.command(name="quest_skill", description="Attempt a SKILL quest roll.")
async def quest_skill(interaction: discord.Interaction):
    # Shared guards: has quest, not completed, type = SKILL
    player, template = await _ensure_active_daily(
        interaction,
        expected_type=QuestType.SKILL
    )
    if player is None:
        return

    # Optional channel restriction
    required_channel = template.required_channel_id
    if required_channel and interaction.channel_id != required_channel:
        await interaction.response.send_message(
            f"❌ You must attempt this training in <#{required_channel}>.",
            ephemeral=True
        )
        return

    dc = template.dc or 10
    roll = random.randint(1, 20)
    success = roll >= dc

    if success:
        gained = template.points_on_success or template.points or 0
        result_text = f"🎯 You rolled **{roll}** (DC {dc}) — **Success!**"
    else:
        gained = template.points_on_fail or 0
        result_text = f"💥 You rolled **{roll}** (DC {dc}) — **You fall short.**"

    quest_manager.complete_daily(interaction.user.id)

    if gained > 0:
        faction_id = get_member_faction_id(interaction.user)
        quest_manager.award_points(interaction.user.id, gained, faction_id)
        await refresh_quest_board(interaction.client)

    msg = result_text
    if gained > 0:
        msg += f"\n\n✨ You earned **{gained}** guild points."
    else:
        msg += "\n\nYou didn't earn any points this time, but the effort still counts for your daily quest."

    await interaction.response.send_message(msg)

@bot.tree.command(name="quest_checkin", description="Complete a TRAVEL quest by checking in at the right location.")
async def quest_checkin(interaction: discord.Interaction):
    # Has quest, not completed, correct type = TRAVEL
    player, template = await _ensure_active_daily(
        interaction,
        expected_type=QuestType.TRAVEL
    )
    if player is None:
        return

    required_channel = template.required_channel_id or 0
    if required_channel and interaction.channel_id != required_channel:
        await interaction.response.send_message(
            f"❌ You must check in at <#{required_channel}> for this quest.",
            ephemeral=True
        )
        return

    quest_manager.complete_daily(interaction.user.id)

    faction_id = get_member_faction_id(interaction.user)
    quest_manager.award_points(interaction.user.id, template.points, faction_id)
    await refresh_quest_board(interaction.client)

    await interaction.response.send_message(
        f"🚶 You check in at your destination.\n\n"
        f"✨ **Quest complete!** You earned **{template.points}** guild points."
    )

@bot.tree.command(name="quest_fetch", description="Collect the required item for a FETCH quest.")
async def quest_fetch(interaction: discord.Interaction):
    # Has quest, not completed, correct type = FETCH
    player, template = await _ensure_active_daily(
        interaction,
        expected_type=QuestType.FETCH
    )
    if player is None:
        return

    source_channel = template.source_channel_id or 0
    if source_channel and interaction.channel_id != source_channel:
        await interaction.response.send_message(
            f"❌ You can only gather this in <#{source_channel}>.",
            ephemeral=True
        )
        return

    quest_id = player.daily_quest.get("quest_id")

    if player.has_item_for_quest(quest_id):
        await interaction.response.send_message(
            "📦 You've already gathered this quest item. "
            "Head to the quest board and use `/quest_turnin`.",
            ephemeral=True
        )
        return

    item_name = template.item_name or "Quest Item"
    player.add_item(quest_id, item_name)
    quest_manager.save_players()

    turnin_channel = template.turnin_channel_id or 0
    turnin_hint = (
        f"<#{turnin_channel}> with `/quest_turnin`"
        if turnin_channel
        else "`/quest_turnin` in the quest board channel"
    )

    await interaction.response.send_message(
        f"📦 You gather **{item_name}**.\n\n"
        f"Now take it to {turnin_hint} to complete your quest."
    )

@bot.tree.command(name="quest_turnin", description="Turn in the collected item for your FETCH quest.")
async def quest_turnin(interaction: discord.Interaction):
    # Has quest, not completed, correct type = FETCH
    player, template = await _ensure_active_daily(
        interaction,
        expected_type=QuestType.FETCH
    )
    if player is None:
        return

    turnin_channel = template.turnin_channel_id or 0
    if turnin_channel and interaction.channel_id != turnin_channel:
        await interaction.response.send_message(
            f"❌ You must turn this in at <#{turnin_channel}>.",
            ephemeral=True
        )
        return

    quest_id = player.daily_quest.get("quest_id")

    if not player.has_item_for_quest(quest_id):
        await interaction.response.send_message(
            "❌ You don't have the required quest item yet. "
            "Use `/quest_fetch` in the correct channel first.",
            ephemeral=True
        )
        return

    # Consume the item and complete the quest
    player.consume_item_for_quest(quest_id)
    quest_manager.save_players()

    quest_manager.complete_daily(interaction.user.id)

    faction_id = get_member_faction_id(interaction.user)
    quest_manager.award_points(interaction.user.id, template.points, faction_id)
    await refresh_quest_board(interaction.client)

    item_name = template.item_name or "Quest Item"

    await interaction.response.send_message(
        f"📬 You turn in **{item_name}** to the guild.\n\n"
        f"✨ **Quest complete!** You earned **{template.points}** guild points."
    )

@bot.tree.command(name="quest_profile", description="View your Jolly Fox Guild badge and quest history.")
async def quest_profile(interaction: discord.Interaction):
    user = interaction.user
    player = quest_manager.get_player(interaction.user.id)

    if not player:
        await interaction.response.send_message(
            f"**🦊 Guild Badge — {interaction.user.display_name}**\n"
            "No profile found.\n"
            "Use `/quest_today` to begin your guild journey.",
            ephemeral=False
        )
        return

    daily = player.daily_quest or {}

    lines = []
    lines.append(f"**🛡️ Jolly Fox Guild Badge — {user.display_name}**\n")

    # -----------------------------
    # LEVEL + XP
    # -----------------------------
    xp_needed = player.level * 20
    lines.append(f"**Level:** {player.level}")
    lines.append(f"**XP:** {player.xp}/{xp_needed}")

    bar_fill = int((player.xp / xp_needed) * 10)
    bar = "█" * bar_fill + "░" * (10 - bar_fill)
    lines.append(f"**Progress:** `{bar}`")
    lines.append("")

    # -----------------------------
    # FACTION (role-based)
    # -----------------------------
    faction_id = get_member_faction_id(user)

    if faction_id:
        fac = get_faction(faction_id)
        if fac:
            lines.append(f"**Faction:** {fac.emoji} {fac.name}")
        else:
            lines.append(f"**Faction:** (Unknown faction `{faction_id}`)")
    else:
        lines.append("**Faction:** None (You have not joined a faction yet.)")

    lines.append("")

    # -----------------------------
    # QUEST HISTORY STATS
    # -----------------------------
    lines.append("**Quest History:**")
    lines.append(f"• Lifetime Quests Completed: **{player.lifetime_completed}**")
    lines.append(f"• Seasonal Quests Completed: **{player.season_completed}**")
    lines.append("")



# Sync
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    cmds = await bot.tree.sync(guild=guild)
    print(f"Synced {len(cmds)} commands to guild {GUILD_ID}")
    print(f"Logged in as {bot.user}")

@bot.event
async def on_member_remove(member: discord.Member):
    user_id = member.id
    if quest_manager.clear_player(user_id):
        print(f"[CLEANUP] Removed player data for {member.display_name} ({user_id})")

# Run
bot.run(TOKEN)
