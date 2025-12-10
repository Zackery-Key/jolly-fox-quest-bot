import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # Jolly Fox server ID from Railway

if GUILD_ID is None:
    raise ValueError("GUILD_ID environment variable is not set!")

GUILD_ID = int(GUILD_ID)

intents = discord.Intents.default()
# default() includes guilds=True, which is enough for slash commands
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    try:
        # Make sure the bot actually sees the Jolly Fox guild
        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            print(
                f"Warning: Bot is not in the guild with ID {GUILD_ID}. "
                "Did you invite it to the Jolly Fox server?"
            )
        else:
            # Sync commands ONLY to Jolly Fox
            await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            print(f"Synced commands to guild: {guild.name} ({guild.id})")

        print("Finished syncing commands.")
    except Exception as e:
        print("Error syncing commands:", e)


@bot.tree.command(name="ping", description="Test that the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🦊 Pong! Jolly Fox is awake!",
        ephemeral=True
    )


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
