import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

@bot.tree.command(name="ping", description="Test that the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🦊 Pong! Jolly Fox is awake!", ephemeral=True)

@bot.tree.command(name="quest_today", description="See your daily Jolly Fox guild quest.")
async def quest_today(interaction: discord.Interaction):
    # For now this is just a placeholder.
    # Later we'll plug in the real quest system here.
    await interaction.response.send_message(
        "**[Daily Quest Placeholder]**\n"
        "There’s no real quest system wired up yet, but the bot is listening!\n"
        "_Next step: we’ll make this actually assign a quest just for you._",
        ephemeral=True
    )

bot.run(TOKEN)
