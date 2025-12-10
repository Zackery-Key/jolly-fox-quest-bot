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


# Commands
@bot.tree.command(name="qtest", description="Test QuestManager connection.")
async def qtest(interaction: discord.Interaction):
    p = quest_manager.get_player(interaction.user.id)
    await interaction.response.send_message(
        f"QTEST OK — Player loaded. Daily quest: {p.daily_quest}",
        ephemeral=True
    )


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


@bot.tree.command(
    name="quest_today",
    description="See your daily Jolly Fox guild quest."
)
async def quest_today(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    # Assign or fetch today's quest
    quest_id = quest_manager.assign_daily(user_id)
    template = quest_manager.get_template(quest_id)

    if template is None:
        await interaction.response.send_message(
            "⚠️ Error loading your quest. No templates found.",
            ephemeral=True
        )
        return

    # Build message text
    msg = (
        f"**🦊 Your Daily Quest:** `{template.name}`\n\n"
        f"**Summary:** {template.summary}\n\n"
        f"**Type:** `{template.type}`\n"
        f"Use the appropriate command to complete it.\n\n"
        f"Quest ID: `{template.quest_id}`"
    )

    await interaction.response.send_message(msg, ephemeral=True)


@bot.tree.command(name="quest_npc", description="Speak with the required NPC to complete your quest.")
async def quest_npc(interaction: discord.Interaction):
    user_id = interaction.user.id
    player = quest_manager.get_player(user_id)

    # 1) Require an active quest
    if not player.daily_quest:
        await interaction.response.send_message(
            "🦊 You don't have an active quest today. Use `/quest_today` first.",
            ephemeral=True
        )
        return

    # 2) Prevent multiple completions (this is what SKILL already does)
    if player.daily_quest.get("completed"):
        await interaction.response.send_message(
            "✅ You've already completed today's quest.",
            ephemeral=True
        )
        return

    quest_id = player.daily_quest.get("quest_id")
    template = quest_manager.get_template(quest_id)

    # 3) Type check: must be SOCIAL
    if template.type != QuestType.SOCIAL:
        await interaction.response.send_message(
            "❌ This is not a SOCIAL quest. Use the correct command for this quest type.",
            ephemeral=True
        )
        return

    # 4) Enforce required channel
    required_channel = template.required_channel_id
    if required_channel and interaction.channel_id != required_channel:
        await interaction.response.send_message(
            f"❌ You must speak with **{template.npc_id}** in <#{required_channel}>.",
            ephemeral=True
        )
        return

    # 5) Load NPC
    npc = quest_manager.get_npc(template.npc_id)
    if npc is None:
        await interaction.response.send_message(
            f"⚠️ Error: NPC `{template.npc_id}` not found.",
            ephemeral=True
        )
        return

    # 6) Mark quest complete
    quest_manager.complete_daily(user_id)

    # 7) Award points once
    quest_manager.quest_board.add_points(template.points)
    quest_manager.save_board()

    # 8) NPC reply
    reply_text = npc.default_reply or "They acknowledge your presence."

    await interaction.response.send_message(
        f"**{npc.name}** says:\n> {reply_text}\n\n"
        f"✨ **Quest complete!** You earned **{template.points}** guild points.",
        ephemeral=True
    )

    user_id = interaction.user.id
    player = quest_manager.get_player(user_id)

    # No active quest
    if not player.daily_quest:
        await interaction.response.send_message(
            "🦊 You don't have an active quest today. Use `/quest_today` first.",
            ephemeral=True
        )
        return

    quest_id = player.daily_quest.get("quest_id")
    template = quest_manager.get_template(quest_id)

    # Not a SOCIAL quest
    if template.type != QuestType.SOCIAL:
        await interaction.response.send_message(
            "❌ This is not a SOCIAL quest. Use the correct command for this quest type.",
            ephemeral=True
        )
        return

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
    quest_manager.complete_daily(user_id)

    # Award points
    quest_manager.quest_board.add_points(template.points)
    quest_manager.save_board()

    # NPC reply
    reply_text = npc.default_reply or "They acknowledge your presence."

    await interaction.response.send_message(
        f"**{npc.name}** says:\n> {reply_text}\n\n"
        f"✨ **Quest complete!** You earned **{template.points}** guild points.",
        ephemeral=True
    )


@bot.tree.command(name="quest_skill", description="Attempt a SKILL quest roll.")
async def quest_skill(interaction: discord.Interaction):
    user_id = interaction.user.id
    player = quest_manager.get_player(user_id)

    if not player.daily_quest:
        await interaction.response.send_message(
            "🦊 You don't have an active quest today. Use `/quest_today` first.",
            ephemeral=True
        )
        return

    if player.daily_quest.get("completed"):
        await interaction.response.send_message(
            "✅ You've already completed today's quest.",
            ephemeral=True
        )
        return

    quest_id = player.daily_quest.get("quest_id")
    template = quest_manager.get_template(quest_id)

    if template.type != QuestType.SKILL:
        await interaction.response.send_message(
            "❌ Your current quest is not a SKILL quest. Use the correct command for your quest type.",
            ephemeral=True
        )
        return

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

    quest_manager.complete_daily(user_id)

    if gained > 0:
        quest_manager.quest_board.add_points(gained)
        quest_manager.save_board()

    msg = result_text
    if gained > 0:
        msg += f"\n\n✨ You earned **{gained}** guild points."
    else:
        msg += "\n\nYou didn't earn any points this time, but the effort still counts for your daily quest."

    await interaction.response.send_message(msg, ephemeral=True)


# Sync
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    cmds = await bot.tree.sync(guild=guild)
    print(f"Synced {len(cmds)} commands to guild {GUILD_ID}")
    print(f"Logged in as {bot.user}")


# Run
bot.run(TOKEN)
