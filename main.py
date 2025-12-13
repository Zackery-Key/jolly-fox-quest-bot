# ========= Imports =========

import os
import random
import discord
from discord.ext import commands
import io
import json

from systems.quests.npc_models import get_npc_quest_dialogue
from systems.quests.quest_manager import QuestManager
from systems.quests.quest_models import QuestType, QuestTemplate
from systems.quests.factions import get_faction, FACTIONS
from systems.quests.npc_models import NPC
from systems.quests import storage
from systems.quests.storage import QUESTS_FILE
from discord import app_commands
from datetime import date


# ========= Constants / IDs =========

# Faction role mapping
SHIELDBORNE_ROLE_ID = 1447646082459762761
SPELLFIRE_ROLE_ID   = 1447646480889548800
VERDANT_ROLE_ID     = 1447644562397859921
FACTION_ROLE_IDS = {
    "shieldborne": SHIELDBORNE_ROLE_ID,
    "spellfire":   SPELLFIRE_ROLE_ID,
    "verdant":     VERDANT_ROLE_ID,
}

# Quest Manager
quest_manager = QuestManager()
print("QUEST MANAGER INITIALIZED")

# Env
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))

if not TOKEN or not GUILD_ID:
    raise ValueError("Missing DISCORD_TOKEN or GUILD_ID environment variable.")


# ========= Bot Setup =========

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)



# ========= Shared Helpers =========

def get_member_faction_id(member: discord.Member) -> str | None:
    """Return the faction_id for this member based on their Discord roles."""
    role_ids = {role.id for role in member.roles}
    for faction_id, rid in FACTION_ROLE_IDS.items():
        if rid in role_ids:
            return faction_id
    return None

def make_progress_bar(value: int, max_value: int, length: int = 20) -> str:
    """Simple text progress bar for embeds."""
    if max_value <= 0:
        max_value = 1

    ratio = max(0.0, min(1.0, value / max_value))
    filled = int(ratio * length)
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}]"

def build_board_embed():
    """Build the quest board embed including faction standings."""
    stats = quest_manager.get_scoreboard()
    board = quest_manager.quest_board

    global_points = stats["global_points"]
    lifetime_completed = stats["lifetime_completed"]
    season_completed = stats["season_completed"]

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

    # Faction standings
    faction_points = board.faction_points or {}
    faction_lines: list[str] = []

    max_pts = max(faction_points.values()) if faction_points else 0
    leaders = {
        fid
        for fid, pts in faction_points.items()
        if pts == max_pts and max_pts > 0
    }

    for faction_id, fac in FACTIONS.items():
        pts = faction_points.get(faction_id, 0)
        crown = " 👑" if faction_id in leaders else ""
        faction_lines.append(f"{fac.emoji} **{fac.name}** — {pts} pts{crown}")

    if not faction_lines:
        faction_lines.append("No faction points yet. Get questing!")

    embed.add_field(
        name="⚔️ Faction Standings",
        value="\n".join(faction_lines),
        inline=False,
    )

    # Quest counts
    embed.add_field(
        name="🏆 Quests Completed This Season",
        value=str(season_completed),
        inline=True,
    )
    embed.add_field(
        name="🌟 Lifetime Quests Completed (All Players)",
        value=str(lifetime_completed),
        inline=True,
    )

    embed.set_footer(
        text="Every completed quest pushes the Jolly Fox further this season."
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

    # Faction info
    faction = get_faction(player.faction_id)
    faction_name = faction.name if faction else "None"
    faction_icon = faction.emoji if faction else "❔"

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
        inline=True,
    )

    embed.add_field(
        name="🎯 Daily Quest",
        value=dq_text,
        inline=False,
    )

    embed.add_field(
        name="🏆 Quest Completion",
        value=(
            f"**Seasonal Completed:** {player.season_completed}\n"
            f"**Lifetime Completed:** {player.lifetime_completed}"
        ),
        inline=True,
    )

    embed.add_field(
        name="🎒 Inventory",
        value=inv_text,
        inline=False,
    )

    embed.set_footer(text="Jolly Fox Guild — Adventure Awaits")

    return embed

async def refresh_quest_board(bot: commands.Bot):
    """Update the existing quest board message if we have one saved."""
    board = quest_manager.quest_board

    if not board.display_channel_id or not board.message_id:
        return

    try:
        channel = bot.get_channel(board.display_channel_id)
        if channel is None:
            channel = await bot.fetch_channel(board.display_channel_id)

        msg = await channel.fetch_message(board.message_id)
        embed = build_board_embed()
        await msg.edit(embed=embed,view=QuestBoardView())

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
        await interaction.response.send_message(
            "You do not have a guild profile yet. Use `/quest_today` to begin.",
            ephemeral=True,
        )
        return None, None

    if not player.daily_quest:
        await interaction.response.send_message(
            "🦊 You don't have an active quest today. Use `/quest_today` first.",
            ephemeral=True,
        )
        return None, None

    if "quest_id" not in player.daily_quest:
        await interaction.response.send_message(
            "⚠️ Your daily quest data is incomplete. Use `/quest_today` to refresh.",
            ephemeral=True,
        )
        return None, None

    if player.daily_quest.get("completed"):
        await interaction.response.send_message(
            "✅ You've already completed today's quest.",
            ephemeral=True,
        )
        return None, None

    quest_id = player.daily_quest.get("quest_id")
    template = quest_manager.get_template(quest_id)

    if template is None:
        await interaction.response.send_message(
            "⚠️ Error: Your quest template could not be found. Please tell an admin.",
            ephemeral=True,
        )
        return None, None

    # Type check (SKILL/SOCIAL/FETCH/TRAVEL)
    if expected_type is not None and template.type != expected_type:
        await interaction.response.send_message(
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
                await interaction.response.send_message(
                    "❌ You don't have the required role to complete this quest.\n"
                    "If you believe this is a mistake, please contact an admin.\n"
                    "You will get a new quest tomorrow with `/quest_today`.",
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
            if "dc" not in q or "points_on_success" not in q:
                return False, f"Skill quest '{qid}' missing dc or points_on_success."

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

        await interaction.response.send_message(
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
            await interaction.response.send_message(
                "🦊 There are no quests available for your current roles right now.\n\n"
                "If you join a new guild faction or RP group later today, "
                "you can try again.",
                ephemeral=True,
            )
            return

    template = quest_manager.get_template(quest_id)
    if template is None:
        await interaction.response.send_message(
            "⚠️ Error loading your quest. Please contact an admin.",
            ephemeral=True,
        )
        return

    completed = bool(player.daily_quest.get("completed"))
    status_label = "✅ COMPLETED" if completed else "🟠 ACTIVE"

    body = f"**Name:** {template.name}\n"

    if template.type == QuestType.SKILL:
        body += f"**Success:** {template.points_on_success or 0} pts\n"
        body += f"**Fail:** {template.points_on_fail or 0} pts\n\n"
    else:
        body += f"**Points:** {template.points}\n\n"

    body += f"**Summary:** {template.summary}\n"

    hint_lines: list[str] = []

    if template.type == QuestType.SOCIAL:
        hint_lines.append(
            f"• Go to <#{template.required_channel_id}> and use `/quest_npc`."
        )
        if template.npc_id:
            hint_lines.append(f"• Required NPC: `{template.npc_id}`")

    elif template.type == QuestType.SKILL:
        hint_lines.append(
            f"• Go to <#{template.required_channel_id}> and use `/quest_skill`."
        )
        if template.dc:
            hint_lines.append(f"• Target DC: **{template.dc}**")

    elif template.type == QuestType.TRAVEL:
        hint_lines.append(
            f"• Go to <#{template.required_channel_id}> and use `/quest_checkin`."
        )

    elif template.type == QuestType.FETCH:
        hint_lines.append(
            f"• Go to <#{template.source_channel_id}> and gather the item with `/quest_fetch`, "
            f"then deliver to <#{template.turnin_channel_id}> and use `/quest_turnin`."
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

    await interaction.response.send_message(msg)

class QuestBoardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🦊 View Daily Quest",
        style=discord.ButtonStyle.primary,
        custom_id="quest_board:view_daily"
    )
    async def view_daily(self, interaction: discord.Interaction, button: discord.ui.Button):
        await send_daily_quest(interaction)

    @discord.ui.button(
        label="📘 View Profile",
        style=discord.ButtonStyle.secondary,
        custom_id="quest_board:view_profile"
    )
    async def view_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = quest_manager.get_or_create_player(interaction.user.id)

        embed = build_profile_embed(
            viewer=interaction.user,
            target=interaction.user,
            player=player,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

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

    await interaction.response.send_message(embed=embed)



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
        f"(ID: {user_id}). They can start fresh with `/quest_today`."
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

@bot.tree.command(name="quest_board", description="Show or update the Jolly Fox seasonal quest scoreboard.")
@app_commands.default_permissions(manage_guild=True)
async def quest_board_cmd(interaction: discord.Interaction):
    board = quest_manager.quest_board
    embed = build_board_embed()

    updated_existing = False

    if board.display_channel_id and board.message_id:
        channel = interaction.client.get_channel(board.display_channel_id)
        try:
            if channel is None:
                channel = await interaction.client.fetch_channel(
                    board.display_channel_id
                )
            msg = await channel.fetch_message(board.message_id)
            await msg.edit(embed=embed, view=QuestBoardView())
            updated_existing = True
        except Exception:
            updated_existing = False

    if not updated_existing:
        await interaction.response.send_message(embed=embed,view=QuestBoardView())

        msg = await interaction.original_response()
        board.display_channel_id = msg.channel.id
        board.message_id = msg.id
        quest_manager.save_board()
    else:
        await interaction.response.send_message(
            "🔄 Updated the existing quest board message.",
            ephemeral=True,
        )

@bot.tree.command(name="quest_admin_set_season",description="Admin: Start a new season and set goal/reward text.")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_set_season(
    interaction: discord.Interaction,
    season_id: str,
    season_goal: int,
    season_reward: str | None = None,
):
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    board = quest_manager.quest_board
    board.reset_season(season_id)
    board.season_goal = max(1, season_goal)
    board.season_reward = season_reward or ""

    quest_manager.save_board()
    await refresh_quest_board(interaction.client)

    await interaction.response.send_message(
        f"✅ Season set to **{season_id}** with goal **{board.season_goal}** points.",
        ephemeral=True,
    )

@bot.tree.command(name="quest_admin_set_board_meta",description="Admin: Edit the seasonal goal or reward text without resetting points.")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_set_board_meta(
    interaction: discord.Interaction,
    season_goal: int | None = None,
    season_reward: str | None = None,
):
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    if season_goal is None and season_reward is None:
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

    quest_manager.save_board()
    await refresh_quest_board(interaction.client)

    await interaction.response.send_message(
        "✅ Quest board metadata updated.",
        ephemeral=True,
    )

@bot.tree.command(name="quest_admin_reset_board",description="Admin: Reset the current season (board + player seasonal stats).")
@app_commands.default_permissions(manage_guild=True)
async def quest_admin_reset_board(interaction: discord.Interaction):
    if not require_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)

    board = quest_manager.quest_board

    # 🔄 RESET BOARD STATE
    board.global_points = 0
    board.faction_points = {}

    # 🔄 RESET PLAYER SEASONAL STATS
    for player in quest_manager.players.values():
        player.season_completed = 0

    # Persist everything
    quest_manager.save_players()
    quest_manager.save_board()

    await refresh_quest_board(interaction.client)

    await interaction.response.send_message(
        "🧹 **Season reset complete.**\n"
        "• Guild points cleared\n"
        "• Faction standings reset\n"
        "• Player seasonal progress reset\n\n"
        "_Lifetime stats were not affected._",
        ephemeral=True,
    )




# ========= PLAYER: Core =========

@bot.tree.command(name="quest_today",description="See your daily Jolly Fox guild quest.")
async def quest_today(interaction: discord.Interaction):
    await send_daily_quest(interaction)

@bot.tree.command(name="profile", description="View your Jolly Fox Guild profile.")
async def profile(interaction: discord.Interaction):
    player = quest_manager.get_or_create_player(interaction.user.id)

    embed = build_profile_embed(
        viewer=interaction.user,
        target=interaction.user,
        player=player,
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="profile_user",description="View another guild member’s profile.")
async def profile_user(
    interaction: discord.Interaction,
    member: discord.Member,
):
    player = quest_manager.get_or_create_player(member.id)

    embed = build_profile_embed(
        viewer=interaction.user,
        target=member,
        player=player,
    )

    await interaction.response.send_message(embed=embed)


# ========= PLAYER: Quest Actions =========

@bot.tree.command(name="quest_npc",description="Speak with the required NPC to complete your quest.")
async def quest_npc(interaction: discord.Interaction):
    import random

    # Validate daily quest + ensure type = SOCIAL
    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.SOCIAL
    )
    if player is None:
        return

    # Enforce required channel
    required_channel = template.required_channel_id
    if required_channel and interaction.channel_id != required_channel:
        return await interaction.response.send_message(
            f"❌ You must speak with **{template.npc_id}** in <#{required_channel}>.",
            ephemeral=True,
        )

    npc = quest_manager.get_npc(template.npc_id)
    if npc is None:
        return await interaction.response.send_message(
            f"⚠️ Error: NPC `{template.npc_id}` not found.",
            ephemeral=True,
        )

    # -------------------------------------------------------------
    # NPC DIALOGUE SELECTION LOGIC
    # -------------------------------------------------------------
    reply_text = get_npc_quest_dialogue(npc, template)


    # -------------------------------------------------------------
    # Complete quest + award points
    # -------------------------------------------------------------
    quest_manager.complete_daily(interaction.user.id)

    faction_id = get_member_faction_id(interaction.user)
    quest_manager.award_points(interaction.user.id, template.points, faction_id)
    await refresh_quest_board(interaction.client)

    # -------------------------------------------------------------
    # Send message
    # -------------------------------------------------------------
    await send_npc_response(
        interaction,
        npc=npc,
        dialogue=reply_text,
        title="Conversation Complete",
        footer=f"✨ **Quest complete!** You earned **{template.points}** guild points.",
    )

@bot.tree.command(name="quest_skill", description="Attempt a SKILL quest roll.")
async def quest_skill(interaction: discord.Interaction):
    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.SKILL
    )
    if player is None:
        return

    required_channel = template.required_channel_id
    if required_channel and interaction.channel_id != required_channel:
        await interaction.response.send_message(
            f"❌ You must attempt this training in <#{required_channel}>.",
            ephemeral=True,
        )
        return

    dc = template.dc or 10
    roll = random.randint(1, 20)
    success = roll >= dc

    gained = template.points_on_success if success else template.points_on_fail or 0
    result_text = (
        f"🎯 You rolled **{roll}** (DC {dc}) — **Success!**"
        if success else
        f"💥 You rolled **{roll}** (DC {dc}) — **You fall short.**"
    )

    # 📜 Get NPC dialogue FIRST (if any)
    npc = quest_manager.get_npc(template.npc_id) if template.npc_id else None
    dialogue = (
        get_npc_quest_dialogue(npc, template, success=success)
        if npc
        else None
    )

    # ✅ Complete quest
    quest_manager.complete_daily(interaction.user.id)

    if gained > 0:
        faction_id = get_member_faction_id(interaction.user)
        quest_manager.award_points(interaction.user.id, gained, faction_id)
        await refresh_quest_board(interaction.client)

    # 🎭 NPC = embed | ⚙️ No NPC = text
    if npc:
        reply = dialogue or "The training concludes."

        embed = build_npc_embed(
            npc=npc,
            dialogue=f"> {reply}\n\n{result_text}\n\n"
                     f"✨ You earned **{gained}** guild points."
                     if gained > 0 else
                     f"> {reply}\n\n{result_text}",
            title="Training Complete",
        )

        await interaction.response.send_message(embed=embed)

    else:
        msg = result_text
        if gained > 0:
            msg += f"\n\n✨ You earned **{gained}** guild points."
        else:
            msg += "\n\nYou complete the task."

        await interaction.response.send_message(msg)

@bot.tree.command(name="quest_checkin", description="Complete a TRAVEL quest by checking in at the right location.")
async def quest_checkin(interaction: discord.Interaction):
    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.TRAVEL
    )
    if player is None:
        return

    required_channel = template.required_channel_id or 0
    if required_channel and interaction.channel_id != required_channel:
        await interaction.response.send_message(
            f"❌ You must check in at <#{required_channel}> for this quest.",
            ephemeral=True,
        )
        return

    npc = quest_manager.get_npc(template.npc_id) if template.npc_id else None
    dialogue = get_npc_quest_dialogue(npc, template) if npc else None

    quest_manager.complete_daily(interaction.user.id)

    faction_id = get_member_faction_id(interaction.user)
    quest_manager.award_points(interaction.user.id, template.points, faction_id)
    await refresh_quest_board(interaction.client)

    await send_npc_response(
    interaction,
    npc=npc,
    dialogue=dialogue or "You check in at your destination.",
    title="Arrival Confirmed",
    footer=f"✨ **Quest complete!** You earned **{template.points}** guild points.",
    )

@bot.tree.command(name="quest_fetch",description="Collect the required item for a FETCH quest.")
async def quest_fetch(interaction: discord.Interaction):
    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.FETCH
    )
    if player is None:
        return

    source_channel = template.source_channel_id or 0
    if source_channel and interaction.channel_id != source_channel:
        await interaction.response.send_message(
            f"❌ You can only gather this in <#{source_channel}>.",
            ephemeral=True,
        )
        return

    quest_id = player.daily_quest.get("quest_id")

    if player.has_item_for_quest(template.item_name):
        await interaction.response.send_message(
            "📦 You've already gathered this quest item. "
            "Head to the quest board and use `/quest_turnin`.",
            ephemeral=True,
        )
        return

    item_name = template.item_name or "Quest Item"
    player.add_item(item_name)
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
    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.FETCH
    )
    if player is None:
        return

    turnin_channel = template.turnin_channel_id or 0
    if turnin_channel and interaction.channel_id != turnin_channel:
        await interaction.response.send_message(
            f"❌ You must turn this in at <#{turnin_channel}>.",
            ephemeral=True,
        )
        return

    if not player.has_item_for_quest(template.item_name):
        await interaction.response.send_message(
            "❌ You don't have the required quest item yet. "
            "Use `/quest_fetch` in the correct channel first.",
            ephemeral=True,
        )
        return

    # 📜 Get NPC dialogue FIRST (while quest is still active)
    npc = quest_manager.get_npc(template.npc_id) if template.npc_id else None
    dialogue = get_npc_quest_dialogue(npc, template)

    npc_name = npc.name if npc else "The Guild"
    reply = (
        dialogue
        if dialogue
        else f"You turn in **{template.item_name}** to the guild."
    )

    # 📦 Consume item
    player.consume_item(template.item_name)
    quest_manager.save_players()

    # ✅ Complete quest + award points
    quest_manager.complete_daily(interaction.user.id)

    faction_id = get_member_faction_id(interaction.user)
    quest_manager.award_points(interaction.user.id, template.points, faction_id)
    await refresh_quest_board(interaction.client)

    await send_npc_response(
    interaction,
    npc=npc,
    dialogue=reply,
    title="Quest Turn-In",
    footer=f"✨ **Quest complete!** You earned **{template.points}** guild points.",)




# ========= Events =========

@bot.event
async def setup_hook():
    guild = discord.Object(id=GUILD_ID)

    # Copy all global commands into the guild
    bot.tree.copy_global_to(guild=guild)


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


bot.run(TOKEN)
