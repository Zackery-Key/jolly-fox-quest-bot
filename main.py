import os
import discord
from discord.ext import commands

# -----------------------------
# Load Quest Manager
# -----------------------------
from systems.quests.quest_manager import QuestManager
quest_manager = QuestManager()
print("QUEST MANAGER INITIALIZED")
print(discord.__version__)

# -----------------------------
# Environment Setup
# -----------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

if TOKEN is None:
    raise ValueError("DISCORD_TOKEN env variable is not set!")

if GUILD_ID is None:
    raise ValueError("GUILD_ID env variable is not set!")

GUILD_ID = int(GUILD_ID)

# -----------------------------
# Bot Setup
# -----------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------------------
# Command: qtest
# -----------------------------
@bot.tree.command(name="qtest", description="Test QuestManager connection.")
async def qtest(interaction: discord.Interaction):
    p = quest_manager.get_player(interaction.user.id)
    await interaction.response.send_message(
        f"QTEST OK — Player loaded. Daily quest: {p.daily_quest}",
        ephemeral=True
    )
    print(f"/qtest ran for user {interaction.user.display_name}")


# -----------------------------
# Command: ping
# -----------------------------
@bot.tree.command(name="ping", description="Test that the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🦊 Pong! Jolly Fox is awake!",
        ephemeral=True
    )


# -----------------------------
# Command: quest_today (placeholder)
# -----------------------------
@bot.tree.command(
    name="quest_today",
    description="See your daily Jolly Fox guild quest."
)
async def quest_today(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**[Daily Quest Placeholder]**\n"
        "Bot is online and ready for quest system integration.",
        ephemeral=True
    )


# -----------------------------
# Sync Commands on Ready
# -----------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    guild_obj = discord.Object(id=GUILD_ID)

    try:
        # IMPORTANT: clear_commands removed
        cmds = await bot.tree.sync(guild=guild_obj)
        print(f"Synced {len(cmds)} commands to guild: {GUILD_ID}")

    except Exception as e:
        print("Error syncing commands:", e)

    print("Finished syncing commands.")


# -----------------------------
# Run Bot
# -----------------------------
bot.run(TOKEN)
