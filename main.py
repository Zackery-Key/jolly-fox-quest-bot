import os
import discord
from discord.ext import commands
import random
from systems.quests.quest_models import QuestType


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
async def _ensure_active_daily(
    interaction: discord.Interaction,
    expected_type: QuestType | None = None,
):
    """
    Shared guard for daily quest commands.
    - Ensures the user has a daily quest.
    - Ensures it is not already completed.
    - Optionally ensures the quest type matches expected_type.
    Returns (player, template) or (None, None) if it handled the error.
    """
    user_id = interaction.user.id
    player = quest_manager.get_player(user_id)

    # No quest at all
    if not player.daily_quest:
        await interaction.response.send_message(
            "🦊 You don't have an active quest today. Use `/quest_today` first.",
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
            "⚠️ Error: your quest template could not be found. Please tell an admin.",
            ephemeral=True
        )
        return None, None

    # Type mismatch
    if expected_type is not None and template.type != expected_type:
        await interaction.response.send_message(
            f"❌ Your current quest is not a `{expected_type.value}` quest. "
            f"Use the correct command for your quest type.",
            ephemeral=True
        )
        return None, None

    return player, template





# Commands
@bot.tree.command(name="quest_admin_reset_user", description="Admin: clear a user's quest data so they can get a new daily quest.")
async def quest_admin_reset_user(
    interaction: discord.Interaction,
    member: discord.Member
):
    # Permission check
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this command.",
            ephemeral=True
        )
        return

    ok = quest_manager.clear_player(member.id)

    if ok:
        await interaction.response.send_message(
            f"🧹 Cleared quest data for **{member.display_name}**. "
            f"They can now run `/quest_today` to get a new daily quest.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"ℹ️ No quest data was found for **{member.display_name}**.",
            ephemeral=True
        )

    user_id = interaction.user.id
    if user_id in quest_manager.players:
        del quest_manager.players[user_id]
        quest_manager.save_players()
        await interaction.response.send_message(
            "🧹 Your player data was cleared. Run `/quest_today` again.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "No player record found to clear.",
            ephemeral=True
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

    # Title + status
    status_label = "✅ COMPLETED" if completed else "🟠 ACTIVE"
    header = f"**🦊 Your Daily Quest — {status_label}**\n"
    body = (
        f"**Name:** {template.name}\n"
        f"**Type:** `{template.type.value if hasattr(template.type, 'value') else template.type}`\n\n"
        f"**Summary:** {template.summary}\n"
    )

    # Type-specific hint
    hint_lines = []

    # SOCIAL
    if template.type == QuestType.SOCIAL:
        if template.required_channel_id:
            hint_lines.append(
                f"• Go to <#{template.required_channel_id}> and use `/quest_npc`."
            )
        else:
            hint_lines.append("• Use `/quest_npc` in the appropriate RP channel.")
        if template.npc_id:
            hint_lines.append(f"• Required NPC: `{template.npc_id}`")

    # SKILL
    elif template.type == QuestType.SKILL:
        if template.required_channel_id:
            hint_lines.append(
                f"• Go to <#{template.required_channel_id}> and use `/quest_skill`."
            )
        else:
            hint_lines.append("• Use `/quest_skill` to attempt your training roll.")
        if template.dc:
            hint_lines.append(f"• Target DC: **{template.dc}**")

    # Other types (TRAVEL, FETCH, etc.) can be fleshed out later
    else:
        hint_lines.append("• Use the appropriate quest command for this type.")

    # Completed vs not completed footer
    if completed:
        footer = "\n\n✨ You’ve already completed this quest for today. Come back tomorrow for a new one, or ask an admin to reset your quest if you’re testing."
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

    # Complete quest
    quest_manager.complete_daily(interaction.user.id)

    # Award points
    quest_manager.quest_board.add_points(template.points)
    quest_manager.save_board()

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
        quest_manager.quest_board.add_points(gained)
        quest_manager.save_board()

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
    quest_manager.quest_board.add_points(template.points)
    quest_manager.save_board()

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
    quest_manager.quest_board.add_points(template.points)
    quest_manager.save_board()

    item_name = template.item_name or "Quest Item"

    await interaction.response.send_message(
        f"📬 You turn in **{item_name}** to the guild.\n\n"
        f"✨ **Quest complete!** You earned **{template.points}** guild points."
    )



# Sync
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    cmds = await bot.tree.sync(guild=guild)
    print(f"Synced {len(cmds)} commands to guild {GUILD_ID}")
    print(f"Logged in as {bot.user}")


# Run
bot.run(TOKEN)
