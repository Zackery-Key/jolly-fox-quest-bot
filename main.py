import os
import discord
from discord.ext import commands

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



# Sync
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    cmds = await bot.tree.sync(guild=guild)
    print(f"Synced {len(cmds)} commands to guild {GUILD_ID}")
    print(f"Logged in as {bot.user}")


# Run
bot.run(TOKEN)
