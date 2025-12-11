import os
import random
import discord
from discord.ext import commands

from systems.quests.quest_manager import QuestManager
from systems.quests.quest_models import QuestType, QuestTemplate
from systems.quests.factions import get_faction, FACTIONS
from systems.quests.npc_models import NPC
from systems.quests import storage


# --- Faction role mapping (replace with your real IDs) ---
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

# Bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# -------------------------
# Discord setup
# -------------------------
@bot.event
async def setup_hook():
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    print(f"Setup complete for guild {GUILD_ID}")


# -------------------------
# Helper: faction from roles
# -------------------------
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
        await msg.edit(embed=embed)
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



# =========================
# Commands ADMIN
# =========================

@bot.tree.command(name="quest_board", description="Show or update the Jolly Fox seasonal quest scoreboard.",)
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
            await msg.edit(embed=embed)
            updated_existing = True
        except Exception:
            updated_existing = False

    if not updated_existing:
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        board.display_channel_id = msg.channel.id
        board.message_id = msg.id
        quest_manager.save_board()
    else:
        await interaction.response.send_message(
            "🔄 Updated the existing quest board message.",
            ephemeral=True,
        )

@bot.tree.command(name="quest_admin_reset_user", description="Admin: Reset a user's quest profile completely.",)
async def quest_admin_reset_user(
    interaction: discord.Interaction,
    member: discord.Member,
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True,
        )
        return

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

@bot.tree.command(name="quest_admin_cleanup", description="Admin: remove quest profiles for users no longer in the server.",)
async def quest_admin_cleanup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True,
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

# ADMIN Quest
@bot.tree.command(name="quest_admin_list_quests",description="Admin: List all quest templates.",)
async def quest_admin_list_quests(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True,
        )
        return

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

@bot.tree.command(name="quest_admin_add_social_quest",description="Admin: Create or update a SOCIAL quest (NPC interaction).",)
async def quest_admin_add_social_quest(
    interaction: discord.Interaction,
    quest_id: str,
    name: str,
    points: int,
    required_channel: discord.TextChannel,
    npc_id: str,
    summary: str,
    details: str | None = None,
    restricted_role: discord.Role | None = None,
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    # Validate quest type
    qtype = QuestType.SOCIAL

    tmpl = QuestTemplate(
        quest_id=quest_id,
        name=name,
        type=qtype,
        points=points,
        required_channel_id=required_channel.id,
        npc_id=npc_id,
        summary=summary,
        details=details or "",
        tags=["social", "npc"],
        allowed_roles=[restricted_role.id] if restricted_role else [],
    )

    storage.save_template(tmpl)
    quest_manager.quest_templates = storage.load_templates()

    await interaction.response.send_message(
        f"📝 **SOCIAL Quest Saved**\n"
        f"- ID: `{quest_id}`\n"
        f"- Name: **{name}**\n"
        f"- Points: {points}\n"
        f"- Channel: <#{required_channel.id}>\n"
        f"- NPC: `{npc_id}`",
        ephemeral=True,
    )

@bot.tree.command(name="quest_admin_add_skill_quest",description="Admin: Create or update a SKILL quest (training / roll).",)
async def quest_admin_add_skill_quest(
    interaction: discord.Interaction,
    quest_id: str,
    name: str,
    dc: int,
    points_on_success: int,
    points_on_fail: int,
    required_channel: discord.TextChannel,
    summary: str,
    details: str | None = None,
    restricted_role: discord.Role | None = None,
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    qtype = QuestType.SKILL

    tmpl = QuestTemplate(
        quest_id=quest_id,
        name=name,
        type=qtype,
        points=0,  # SKILL uses success/fail only
        dc=dc,
        points_on_success=points_on_success,
        points_on_fail=points_on_fail,
        required_channel_id=required_channel.id,
        summary=summary,
        details=details or "",
        tags=["skill"],
        allowed_roles=[restricted_role.id] if restricted_role else [],
    )

    storage.save_template(tmpl)
    quest_manager.quest_templates = storage.load_templates()

    await interaction.response.send_message(
        f"📝 **SKILL Quest Saved**\n"
        f"- ID: `{quest_id}`\n"
        f"- Name: **{name}**\n"
        f"- DC: {dc}\n"
        f"- Success: {points_on_success} pts\n"
        f"- Fail: {points_on_fail} pts\n"
        f"- Channel: <#{required_channel.id}>",
        ephemeral=True,
    )

@bot.tree.command(name="quest_admin_add_travel_quest",description="Admin: Create or update a TRAVEL quest (check-in).",)
async def quest_admin_add_travel_quest(
    interaction: discord.Interaction,
    quest_id: str,
    name: str,
    points: int,
    required_channel: discord.TextChannel,
    summary: str,
    details: str | None = None,
    restricted_role: discord.Role | None = None,
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    qtype = QuestType.TRAVEL

    tmpl = QuestTemplate(
        quest_id=quest_id,
        name=name,
        type=qtype,
        points=points,
        required_channel_id=required_channel.id,
        summary=summary,
        details=details or "",
        tags=["travel"],
        allowed_roles=[restricted_role.id] if restricted_role else [],
    )

    storage.save_template(tmpl)
    quest_manager.quest_templates = storage.load_templates()

    await interaction.response.send_message(
        f"📝 **TRAVEL Quest Saved**\n"
        f"- ID: `{quest_id}`\n"
        f"- Name: **{name}**\n"
        f"- Points: {points}\n"
        f"- Channel: <#{required_channel.id}>",
        ephemeral=True,
    )

@bot.tree.command(name="quest_admin_add_fetch_quest",description="Admin: Create or update a FETCH quest (gather + turn-in).",)
async def quest_admin_add_fetch_quest(
    interaction: discord.Interaction,
    quest_id: str,
    name: str,
    points: int,
    item_name: str,
    source_channel: discord.TextChannel,
    turnin_channel: discord.TextChannel,
    summary: str,
    details: str | None = None,
    restricted_role: discord.Role | None = None,
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    qtype = QuestType.FETCH

    tmpl = QuestTemplate(
        quest_id=quest_id,
        name=name,
        type=qtype,
        points=points,
        item_name=item_name,
        source_channel_id=source_channel.id,
        turnin_channel_id=turnin_channel.id,
        summary=summary,
        details=details or "",
        tags=["fetch"],
        allowed_roles=[restricted_role.id] if restricted_role else [],
    )

    storage.save_template(tmpl)
    quest_manager.quest_templates = storage.load_templates()

    await interaction.response.send_message(
        f"📝 **FETCH Quest Saved**\n"
        f"- ID: `{quest_id}`\n"
        f"- Name: **{name}**\n"
        f"- Points: {points}\n"
        f"- Item: `{item_name}`\n"
        f"- Source: <#{source_channel.id}>\n"
        f"- Turn-in: <#{turnin_channel.id}>",
        ephemeral=True,
    )

@bot.tree.command(name="quest_admin_remove_quest",description="Admin: Delete a quest template by ID.",)
async def quest_admin_remove_quest(
    interaction: discord.Interaction,
    quest_id: str,
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True,
        )
        return

    if quest_id not in quest_manager.quest_templates:
        await interaction.response.send_message(
            f"❌ No quest template found with id `{quest_id}`.",
            ephemeral=True,
        )
        return

    storage.delete_template(quest_id)
    quest_manager.quest_templates = storage.load_templates()

    await interaction.response.send_message(
        f"🗑️ Quest template `{quest_id}` has been removed.",
        ephemeral=True,
    )


#ADMIN NPC
@bot.tree.command(name="quest_admin_list_npcs",description="Admin: List all quest NPCs.",)
async def quest_admin_list_npcs(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True,
        )
        return

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

@bot.tree.command(name="quest_admin_add_npc",description="Admin: Create or update a quest NPC.",)
async def quest_admin_add_npc(
    interaction: discord.Interaction,
    npc_id: str,
    name: str,
    avatar_url: str | None = None,
    default_reply: str | None = None,
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True,
        )
        return

    npc = NPC(
        npc_id=npc_id,
        name=name,
        avatar_url=avatar_url or "",
        default_reply=default_reply or "",
    )

    storage.save_npc(npc)
    quest_manager.npcs = storage.load_npcs()

    await interaction.response.send_message(
        f"✅ NPC `{npc_id}` saved as **{name}**.",
        ephemeral=True,
    )

@bot.tree.command(name="quest_admin_remove_npc",description="Admin: Delete a quest NPC by ID.",)
async def quest_admin_remove_npc(
    interaction: discord.Interaction,
    npc_id: str,
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True,
        )
        return

    if npc_id not in quest_manager.npcs:
        await interaction.response.send_message(
            f"❌ No NPC found with id `{npc_id}`.",
            ephemeral=True,
        )
        return

    storage.delete_npc(npc_id)
    quest_manager.npcs = storage.load_npcs()

    await interaction.response.send_message(
        f"🗑️ NPC `{npc_id}` has been removed.",
        ephemeral=True,
    )


#ADMIN Board
@bot.tree.command(name="quest_admin_set_season",description="Admin: Start a new season and set goal/reward text.",)
async def quest_admin_set_season(
    interaction: discord.Interaction,
    season_id: str,
    season_goal: int,
    season_reward: str | None = None,
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True,
        )
        return

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

@bot.tree.command(name="quest_admin_set_board_meta",description="Admin: Edit the seasonal goal or reward text without resetting points.",)
async def quest_admin_set_board_meta(
    interaction: discord.Interaction,
    season_goal: int | None = None,
    season_reward: str | None = None,
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True,
        )
        return

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

@bot.tree.command(name="quest_admin_reset_board",description="Admin: Reset global and faction points for the current season.",)
async def quest_admin_reset_board(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You do not have permission to use this.",
            ephemeral=True,
        )
        return

    board = quest_manager.quest_board
    board.global_points = 0
    board.faction_points = {}

    quest_manager.save_board()
    await refresh_quest_board(interaction.client)

    await interaction.response.send_message(
        "🧹 Quest board points have been reset for the current season.",
        ephemeral=True,
    )


# =========================
# Commands Player
# =========================

@bot.tree.command(name="quest_today",description="See your daily Jolly Fox guild quest.",)
async def quest_today(interaction: discord.Interaction):
    user = interaction.user
    user_id = user.id

    # Collect the user's current Discord role IDs
    role_ids = [role.id for role in getattr(user, "roles", [])]

    quest_id = quest_manager.assign_daily(user_id, role_ids)
    player = quest_manager.get_player(user_id)

    # If no quest is available for current roles
    if quest_id is None:
        await interaction.response.send_message(
            "🦊 There are no quests available for your current roles right now.\n\n"
            "If you join a new guild faction or RP group later today, "
            "you can try `/quest_today` again.",
            ephemeral=True,
        )
        return

    template = quest_manager.get_template(quest_id)

    if template is None:
        await interaction.response.send_message(
            "⚠️ Error loading your quest. No templates found or quest is invalid.",
            ephemeral=True,
        )
        return

    completed = bool(player.daily_quest.get("completed"))

    status_label = "✅ COMPLETED" if completed else "🟠 ACTIVE"
    qtype_str = template.type.value

    header = f"**🦊 Your Daily Quest — {status_label}**\n"

    # Start building body
    body = f"**Name:** {template.name}\n"

    # If SKILL quest → show success/fail scoring
    if template.type == QuestType.SKILL:
        body += f"**Success:** {template.points_on_success or 0} pts\n"
        body += f"**Fail:** {template.points_on_fail or 0} pts\n\n"
    else:
        # All other quest types use the base points value
        body += f"**Points:** {template.points}\n\n"

    # Summary is always shown
    body += f"**Summary:** {template.summary}\n"


    hint_lines: list[str] = []

    if template.type == QuestType.SOCIAL:
        if template.required_channel_id:
            hint_lines.append(
                f"• Go to <#{template.required_channel_id}> and use `/quest_npc`."
            )
        else:
            hint_lines.append("• Use `/quest_npc` in the appropriate RP channel.")
        if template.npc_id:
            hint_lines.append(f"• Required NPC: `{template.npc_id}`")

    elif template.type == QuestType.SKILL:
        if template.required_channel_id:
            hint_lines.append(
                f"• Go to <#{template.required_channel_id}> and use `/quest_skill`."
            )
        else:
            hint_lines.append("• Use `/quest_skill` to attempt your training roll.")
        if template.dc:
            hint_lines.append(f"• Target DC: **{template.dc}**")

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

    else:
        hint_lines.append("• Use the appropriate quest command for this type.")

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

@bot.tree.command(name="quest_npc",description="Speak with the required NPC to complete your quest.",)
async def quest_npc(interaction: discord.Interaction):
    player, template = await _ensure_active_daily(
        interaction, expected_type=QuestType.SOCIAL
    )
    if player is None:
        return

    required_channel = template.required_channel_id
    if required_channel and interaction.channel_id != required_channel:
        await interaction.response.send_message(
            f"❌ You must speak with **{template.npc_id}** in <#{required_channel}>.",
            ephemeral=True,
        )
        return

    npc = quest_manager.get_npc(template.npc_id)
    if npc is None:
        await interaction.response.send_message(
            f"⚠️ Error: NPC `{template.npc_id}` not found.",
            ephemeral=True,
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

@bot.tree.command(name="quest_skill",description="Attempt a SKILL quest roll.",)
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
        msg += (
            "\n\nYou didn't earn any points this time, but the effort still counts for "
            "your daily quest."
        )

    await interaction.response.send_message(msg)

@bot.tree.command(name="quest_checkin",description="Complete a TRAVEL quest by checking in at the right location.",)
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

    quest_manager.complete_daily(interaction.user.id)

    faction_id = get_member_faction_id(interaction.user)
    quest_manager.award_points(interaction.user.id, template.points, faction_id)
    await refresh_quest_board(interaction.client)

    await interaction.response.send_message(
        f"🚶 You check in at your destination.\n\n"
        f"✨ **Quest complete!** You earned **{template.points}** guild points."
    )

@bot.tree.command(name="quest_fetch",description="Collect the required item for a FETCH quest.",)
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

    if player.has_item_for_quest(quest_id):
        await interaction.response.send_message(
            "📦 You've already gathered this quest item. "
            "Head to the quest board and use `/quest_turnin`.",
            ephemeral=True,
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

@bot.tree.command(name="quest_turnin",description="Turn in the collected item for your FETCH quest.",)
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

    quest_id = player.daily_quest.get("quest_id")

    if not player.has_item_for_quest(quest_id):
        await interaction.response.send_message(
            "❌ You don't have the required quest item yet. "
            "Use `/quest_fetch` in the correct channel first.",
            ephemeral=True,
        )
        return

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

@bot.tree.command(name="quest_profile",description="View your Jolly Fox Guild profile.")
async def quest_profile(interaction: discord.Interaction):
    user = interaction.user
    user_id = user.id

    player = quest_manager.get_or_create_player(user_id)

    # Basic fields
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

    # Daily quest status
    dq = player.daily_quest
    has_dq = bool(dq.get("quest_id"))
    dq_text = ""

    if has_dq:
        qid = dq["quest_id"]
        tmpl = quest_manager.get_template(qid)
        status = "Completed" if dq.get("completed") else "Active"

        if tmpl:
            dq_text = (
                f"**{tmpl.name}**\n"
                f"Status: **{status}**\n"
                f"*{tmpl.summary}*"
            )
        else:
            dq_text = "⚠️ (Quest template missing)"

    else:
        dq_text = "No quest assigned today. Use `/quest_today`."

    # Inventory formatting
    if player.inventory:
        inv_lines = [f"- **{item}** × {qty}" for item, qty in player.inventory.items()]
        inv_text = "\n".join(inv_lines)
    else:
        inv_text = "_Empty_"

    # Seasonal stats
    lifetime = player.lifetime_completed
    seasonal = player.seasonal_completed

    # --- Build Embed ---
    embed = discord.Embed(
        title=f"🦊 {user.display_name} — Guild Profile",
        color=discord.Color.orange(),
    )

    # Thumbnail = avatar
    embed.set_thumbnail(url=user.display_avatar.url)

    # Core stats
    embed.add_field(
        name="📘 Level & Experience",
        value=(
            f"**Level:** {level}\n"
            f"**XP:** {xp} / {next_xp}\n"
            f"`{bar}`"
        ),
        inline=False,
    )

    # Faction
    embed.add_field(
        name="🏅 Faction",
        value=f"{faction_icon} **{faction_name}**",
        inline=True,
    )

    # Daily quest
    embed.add_field(
        name="🎯 Daily Quest",
        value=dq_text,
        inline=False,
    )

    # Progress
    embed.add_field(
        name="🏆 Quest Completion",
        value=(
            f"**Seasonal Completed:** {seasonal}\n"
            f"**Lifetime Completed:** {lifetime}"
        ),
        inline=True,
    )

    # Inventory
    embed.add_field(
        name="🎒 Inventory",
        value=inv_text,
        inline=False,
    )

    embed.set_footer(text="Jolly Fox Guild — Adventure Awaits")

    await interaction.response.send_message(embed=embed)


# Sync on ready
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
