import discord
import asyncio
from discord.ext import commands, tasks
import re
from discord import option
from datetime import datetime, timedelta
import time
from discord import bot
import datetime
from discord import Option, ApplicationContext, Embed, Permissions
import textwrap
import traceback
from datetime import datetime, timezone
import io
import json
import os
from dotenv import load_dotenv
import datetime
from discord import ui
import random
from discord.ui import Modal
from discord import ButtonStyle
from discord import Interaction
from discord.utils import get
from discord.ui import View, Button
import platform
import psutil


intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

status = discord.Status.do_not_disturb
activity = discord.Activity(type=discord.ActivityType.playing, name="/help")

bot = discord.Bot(
    intents=intents,
    debug_guilds=[1416605197492293735],
    status=status,
    activity=activity,

)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

    await bot.sync_commands()

    print("Slash-Commands synchronisiert!")

#-----------------------------------------------------------------------------------------------------------------------
SERVER_NAME = "name it"
BAN_CHANNEL_NAME = ""
LOG_CHANNEL_ID         = 1
BUG_REPORT_CHANNEL_ID = 1  
MUTE_CHANNEL_NAME = ""
RULE_CHANNEL_ID = 1
LOBBY_CHANNEL_ID       = 1
TEMP_CATEGORY_ID       = 1
SUPPORT_ROLE_NAME = ""
WELCOME_CHANNEL_ID = 1
WARN_ROLE_NAME = ""
RAID_LOG_CHANNEL_ID = 1
RAID_JOIN_LIMIT = 5      
RAID_TIME_WINDOW = 1
INVITE_BYPASS_ROLES = [""]
CLEAR_CHANNEL_ID = 1 
TRANSCRIPT_FOLDER = "Clear-scripts"
MOD_ROLE_NAME = ""
WARN_LOG_CHANNEL_ID = 1
BAN_ROLE_NAME = ""
required_role_name = ""


#-----------------------------------------------------------------------------------------------------------------------
                                             # Uptime #

bot_start_time = datetime.datetime.now(datetime.timezone.utc)

@bot.slash_command(name="uptime", description="Zeigt die Laufzeit des Bots an.")
async def uptime(ctx: discord.ApplicationContext):
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = now - bot_start_time
    days, remainder = divmod(delta.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"

    embed = discord.Embed(
        title="⬛Bot Uptime⬛",
        description=f"Der Bot ist seit **{uptime_str}** online.",
        color=discord.Color.from_rgb(0, 0, 0)
    )
    await ctx.respond(embed=embed)

#-----------------------------------------------------------------------------------------------------------------------
                                         #--Invite blocker--#

INVITE_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?(?:discord\.gg|discord(app)?\.com/invite)/[a-zA-Z0-9]+",
    re.IGNORECASE
)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    
    if any(role.name in INVITE_BYPASS_ROLES for role in message.author.roles):
        return

    if INVITE_REGEX.search(message.content):
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} Das Posten von Discord-Einladungslinks ist nicht erlaubt!",
                delete_after=8
            )
        except Exception:
            pass

    await bot.process_commands(message)

#-----------------------------------------------------------------------------------------------------------------------
                                         #--Raid schutz--#                                                   
recent_joins = []

@bot.event
async def on_member_join(member):
    

    
    now = datetime.datetime.now(datetime.timezone.utc)
    recent_joins.append(now)
    
    while recent_joins and (now - recent_joins[0]).total_seconds() > RAID_TIME_WINDOW:
        recent_joins.pop(0)

    if len(recent_joins) >= RAID_JOIN_LIMIT:
        log_channel = bot.get_channel(RAID_LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="🖤 Raid-Verdacht!",
                description=f"In den letzten {RAID_TIME_WINDOW} Sekunden sind {len(recent_joins)} User gejoint!",
                color=discord.Color.from_rgb(0, 0, 0),
                timestamp=now
            )
            embed.set_footer(text="Eclipse Bot • Raid-Schutz")
            await log_channel.send(embed=embed)


#-----------------------------------------------------------------------------------------------------------------------
                                         #--Welcome--#

@bot.event
async def on_member_join(member: discord.Member):
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title=f"🖤 Willkommen auf {member.guild.name}!",
            description=(
                f"Hey {member.mention}!\n\n"
                "Willkommen auf dem Server **Ausfüllen** 🖤\n"
                "Wir wünschen dir eine gute Zeit – bei Fragen steht dir das Team jederzeit zur Seite!\n\n"
            ),
            color=discord.Color.from_rgb(0, 0, 0)
        )
        embed.set_footer(text="Eclipse Bot • Automatische Willkommensnachricht")

        msg = await channel.send(embed=embed)
        async def delete_msg_later(message):
            await asyncio.sleep(60)
            try:
                await message.delete()
            except discord.NotFound:
                pass
        asyncio.create_task(delete_msg_later(msg))

    auto_role_name = "ッSpieler"
    role = discord.utils.find(lambda r: r.name.lower() == auto_role_name.lower(), member.guild.roles)
    if role:
        try:
            await member.add_roles(role, reason="Auto-Role bei Join")
        except discord.Forbidden:
            print(f"🖤 Bot hat keine Berechtigung, die Rolle '{role.name}' zu vergeben!")
        except Exception as e:
            print(f"🖤 Fehler beim Rollen vergeben: {e}")
    else:
        print(f"🖤 Rolle '{auto_role_name}' nicht gefunden!")

#-----------------------------------------------------------------------------------------------------------------------


@bot.slash_command(name="temprole", description="Gibt eine Rolle temporär (Minuten).")
async def temprole(ctx: discord.ApplicationContext, member: discord.Option(discord.Member, "Member"), role: discord.Option(discord.Role, "Rolle"), minutes: discord.Option(int, "Minuten")):
    if not ctx.author.guild_permissions.manage_roles:
        await ctx.respond("🖤 Keine Berechtigung.", ephemeral=True)
        return
    await member.add_roles(role)
    await ctx.respond(f"🖤 Rolle {role.name} gegeben für {minutes} Minuten.", ephemeral=True)
    await asyncio.sleep(max(1, minutes) * 60)
    
    try:
        await member.remove_roles(role)
    except:
        pass

#-----------------------------------------------------------------------------------------------------------------------
                                         #--Ticket system--#
class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🎫 Ticket eröffnen", style=ButtonStyle.green)
    async def open_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        guild = interaction.guild

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites,
            reason="Neues Ticket eröffnet"
        )

        view = ClaimCloseView()
        embed = Embed(
            title="🎟️ Support Ticket",
            description="Ein Teammitglied kann dieses Ticket jetzt claimen oder schließen.",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket eröffnet: {channel.mention}", ephemeral=True)


class ClaimCloseView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="✅ Claim", style=ButtonStyle.primary)
    async def claim(self, button: discord.ui.Button, interaction: discord.Interaction):
        support_role = get(interaction.guild.roles, name=SUPPORT_ROLE_NAME)
        if support_role in interaction.user.roles:
            await interaction.channel.send(f"👮 {interaction.user.mention} hat dieses Ticket geclaimt.")
            await interaction.response.defer()
        else:
            await interaction.response.send_message("❌ Du hast keine Berechtigung zum Claimen.", ephemeral=True)

    @ui.button(label="❌ Ticket schließen", style=ButtonStyle.danger)
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        support_role = get(interaction.guild.roles, name=SUPPORT_ROLE_NAME)
        if support_role in interaction.user.roles:
            await interaction.channel.delete(reason="Ticket geschlossen")
        else:
            await interaction.response.send_message("❌ Du darfst dieses Ticket nicht schließen.", ephemeral=True)


@bot.command()
async def ticket(ctx):
    view = TicketView()
    await ctx.send("🎫 Klicke auf den Button unten, um ein Support-Ticket zu eröffnen:", view=view)

#-----------------------------------------------------------------------------------------------------------------------
                                         #--/nachricht--#
@bot.command()
async def nachricht(ctx, user: discord.User, *, inhalt):
    try:
        await user.send(inhalt)
        await ctx.send(f"Nachricht an {user.name} wurde gesendet! 🖤", ephemeral=True)
    except discord.Forbidden:
        await ctx.send("Ich kann dem Benutzer keine Nachricht schicken – wahrscheinlich hat er DMs deaktiviert. 🖤")

#-----------------------------------------------------------------------------------------------------------------------
                                         #--/invites--#

@bot.slash_command(name="invites", description="Zeigt alle Einladungen eines Members als Liste.")
async def invites(
    ctx: discord.ApplicationContext,
    member: discord.Option(discord.Member, "Wessen Einladungen?", required=False)
):
    member = member or ctx.user
    invites = await ctx.guild.invites()
    user_invites = [invite for invite in invites if invite.inviter and invite.inviter.id == member.id]

    if not user_invites:
        await ctx.respond(f"{member.mention} hat keine aktiven Einladungen.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"Einladungen von {member.display_name}",
        color=discord.Color.from_rgb(0, 0, 0)
    )
    for invite in user_invites:
        embed.add_field(
            name=f"Code: `{invite.code}`",
            value=f"Verwendet: **{invite.uses}x**\nErstellt am: {invite.created_at.strftime('%d.%m.%Y') if invite.created_at else 'Unbekannt'}",
            inline=False
        )
    await ctx.respond(embed=embed, ephemeral=True)                                             


@bot.slash_command(name="inviteleaderboard", description="Zeigt das Einladungs-Leaderboard des Servers.")
async def inviteleaderboard(ctx: discord.ApplicationContext):
    invites = await ctx.guild.invites()
    leaderboard = {}

    for invite in invites:
        if invite.inviter:
            leaderboard[invite.inviter.id] = leaderboard.get(invite.inviter.id, 0) + invite.uses

    if not leaderboard:
        await ctx.respond("Es gibt noch keine Einladungen auf diesem Server.", ephemeral=True)
        return

    
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]

    embed = discord.Embed(
        title="🏆 Invite Leaderboard",
        description="Top 10 Mitglieder mit den meisten Einladungen:",
        color=discord.Color.from_rgb(0, 0, 0)
    )

    for i, (user_id, count) in enumerate(sorted_leaderboard, 1):
        member = ctx.guild.get_member(user_id)
        name = member.mention if member else f"<@{user_id}>"
        embed.add_field(name=f"{i}. {name}", value=f"Einladungen: **{count}**", inline=False)

    await ctx.respond(embed=embed)
#-----------------------------------------------------------------------------------------------------------------------
                                         #--/Ship--#


@bot.slash_command(
    name="ship",
    description="Berechnet die Kompatibilität zweier Mitglieder 🖤."
)
@option("user1", discord.Member, description="Erste Person")
@option("user2", discord.Member, description="Zweite Person")
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    
    if user1.id == user2.id:
        await ctx.respond(f"Du kannst **{user1.display_name}** nicht mit dir selbst shippen! 😅", ephemeral=True)
        return

    
    score = random.randint(0, 100)

    
    if score < 30:
        text = "Das passt leider gar nicht..."
    elif score < 70:
        text = "Könnte was werden..."
    else:
        text = "Ihr seid ein Traumpaar! 🖤"

    
    name1 = user1.display_name[:len(user1.display_name) // 2]
    name2 = user2.display_name[len(user2.display_name) // 2:]
    ship_name = f"{name1}{name2}"

    
    embed = discord.Embed(
        title="🖤 Ship Generator 🖤",
        description=f"**{user1.mention} + {user2.mention} = {ship_name}**\n\n{score}% - {text}"
    )
    embed.set_thumbnail(url=user1.avatar.url if user1.avatar else user1.default_avatar.url)
    embed.set_image(url=user2.avatar.url if user2.avatar else user2.default_avatar.url)

    
    await ctx.respond(embed=embed)
















#-----------------------------------------------------------------------------------------------------------------------

@bot.slash_command(name="diagnose", description="Zeigt Diagnose-Informationen zum Bot.")
async def diagnose(ctx: discord.ApplicationContext):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / 1024 / 1024  # MB
    cpu = process.cpu_percent(interval=0.5)
    python_version = platform.python_version()
    dpy_version = discord.__version__
    uptime = datetime.datetime.now(datetime.timezone.utc) - bot_start_time

    embed = discord.Embed(
        title="🤍 Bot Diagnose",
        color=discord.Color.from_rgb(0, 0, 0)
    )
    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)} ms", inline=True)
    embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=True)
    embed.add_field(name="Speicher", value=f"{mem:.2f} MB", inline=True)
    embed.add_field(name="CPU", value=f"{cpu:.1f}%", inline=True)
    embed.add_field(name="Python", value=python_version, inline=True)
    embed.add_field(name="discord.py", value=dpy_version, inline=True)
    embed.add_field(name="Server", value=f"{len(bot.guilds)}", inline=True)
    embed.set_footer(text="Eclipse • Diagnose")

    await ctx.respond(embed=embed, ephemeral=True)









#-----------------------------------------------------------------------------------------------------------------------
                                         #--/Hilfe--#

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Hilfemenü", color=discord.Color.from_rgb(0, 0, 0))
    embed.add_field(name="/info", value="🖤Zeigt die Latenz an.", inline=False)
    embed.add_field(name="/serverinfo", value="🖤Zeigt die server information.", inline=False)
    embed.add_field(name="/mcreport", value="🖤Reporte ein ingame bug.", inline=False)
    embed.add_field(name="/temphilfe", value="🖤hilfemenü für denn tempvoice.", inline=False)
    await ctx.send(embed=embed)


#-----------------------------------------------------------------------------------------------------------------------
                                         #--/Giveaway--#

giveaways: dict[int, dict] = {}
tasks: dict[int, asyncio.Task] = {}

@bot.slash_command(
    name="giveaway",
    description="Startet ein Giveaway"
)
async def giveaway(
    ctx: discord.ApplicationContext,
    dauer: Option(int, "Dauer des Giveaways in Minuten"),
    preis: Option(str, "Was wird verlost?"),
    invite_voraussetzung: Option(int, "Wie viele Invites werden benötigt?", default=0)
):
    await ctx.defer(ephemeral=True)

    end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=dauer)
    timestamp = f"<t:{int(end_time.timestamp())}:R>"

    embed = discord.Embed(
        title="🖤 Giveaway gestartet!",
        color=discord.Color.from_rgb(0, 0, 0),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="🖤 Preis", value=preis, inline=False)
    embed.add_field(name="🖤 Endet", value=timestamp, inline=False)

    if invite_voraussetzung > 0:
        embed.add_field(
            name="🖤 Voraussetzung",
            value=f"{invite_voraussetzung} Einladungen",
            inline=False
        )

    embed.add_field(
        name="🖤 Teilnahme",
        value="Reagiere mit dem Emoji, um teilzunehmen!",
        inline=False
    )
    embed.set_footer(text="By Eclipse")

    message = await ctx.channel.send(embed=embed)
    await message.add_reaction("🖤")

    giveaways[message.id] = {
        "end_time": end_time,
        "preis": preis,
        "invite_min": invite_voraussetzung,
        "channel_id": ctx.channel.id,
        "message_id": message.id,
        "host": ctx.author.id
    }

    await ctx.respond("Giveaway gestartet!", ephemeral=True)

    tasks[message.id] = asyncio.create_task(monitor_giveaway(message.id))


async def monitor_giveaway(message_id: int):
    await asyncio.sleep(60)

    while True:
        data = giveaways.get(message_id)
        if not data:
            return

        if datetime.datetime.utcnow() >= data["end_time"]:
            channel = bot.get_channel(data["channel_id"])
            if not channel:
                return

            try:
                message = await channel.fetch_message(data["message_id"])
                reaction = discord.utils.get(message.reactions, emoji="🖤")

                if not reaction:
                    await channel.send("🖤 Es gab keine Teilnehmer für das Giveaway.")
                    giveaways.pop(message_id, None)
                    tasks.pop(message_id, None)
                    return

                users = [u async for u in reaction.users() if not u.bot]

                if data["invite_min"] > 0:
                    invites = await channel.guild.invites()
                    valid = []
                    for user in users:
                        total_uses = sum(inv.uses for inv in invites
                                         if inv.inviter and inv.inviter.id == user.id)
                        if total_uses >= data["invite_min"]:
                            valid.append(user)
                    users = valid

                if users:
                    winner = random.choice(users)
                    await channel.send(
                        f"🖤 Glückwunsch {winner.mention}, du hast **{data['preis']}** gewonnen!"
                    )
                else:
                    await channel.send("🖤 Es gab keine gültigen Teilnehmer.")

                giveaways.pop(message_id, None)
                tasks.pop(message_id, None)
            except Exception as e:
                print(f"Fehler beim Abschließen des Giveaways: {e}")
            return

        await asyncio.sleep(60)


#-----------------------------------------------------------------------------------------------------------------------
                                         #--/Teamhelp--#

@bot.command()
async def teamhelp(ctx):


    if discord.utils.get(ctx.author.roles, name=required_role_name) is None:
        return await ctx.send("🖤 Du hast keine Berechtigung, diesen Befehl zu verwenden.", delete_after=10)

    embed = discord.Embed(title="Hilfemenü", color=discord.Color.from_rgb(0, 0, 0))
    embed.add_field(name="/report", value="🖤Auch teamler müssen bug reports machen.", inline=False)
    embed.add_field(name="/ban", value="🖤 Bannt einen spieler mit log eintrag.", inline=False)
    embed.add_field(name="/unban", value="🖤 Entbannt einen spieler (user id wichtig).", inline=False)
    embed.add_field(name="/timeout", value="🖤Mutet einen member mit log eintrag.", inline=False)
    embed.add_field(name="/untimeout", value="🖤Unmutet einen member.",inline = False)
    embed.add_field(name="/slowmode", value="🖤Stellt slowmode in sekunden ein.", inline=False)
    embed.add_field(name="/modlog", value="🖤 Moderations  verlauf timeout ban usw.. only admin.", inline=False)
    embed.add_field(name="/userinfo", value="🖤 Gibt Informationen über einen Spieler.", inline=False)
    embed.add_field(name="/clear", value="🖤 Cleart den Chat.", inline=False)
    embed.add_field(name="/embednachricht", value="🖤 sendet eine bot admin Nachricht.", inline=False)
    embed.add_field(name="/embed", value="🖤 Erstell ein embed.", inline=False)
    embed.add_field(name="/warn", value="🖤 Warnt ein member mit log eintrag.", inline=False)
    embed.add_field(name="/warnremove", value="🖤 Entfernt denn warn + log eintrag.", inline=False)
    embed.add_field(name="/giveaway", value="🖤 erstellt ein giveaway.", inline=False)
    await ctx.send(embed=embed)




#-----------------------------------------------------------------------------------------------------------------------
                                         #--/info /serverinfo--#



@bot.slash_command(name="info", description="Zeigt Infos über den Bot.")
async def info(ctx: discord.ApplicationContext):
    embed = discord.Embed(title="Bot Info", description="Hier sind einige Details:", color=discord.Color.from_rgb(0, 0, 0))
    embed.add_field(name="Name", value=bot.user.name)
    embed.add_field(name="ID", value=bot.user.id)
    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)} ms")
    await ctx.respond(embed=embed)

@bot.slash_command(name="serverinfo", description="Zeigt Infos über den Server.")
async def serverinfo(ctx: discord.ApplicationContext):
    guild = ctx.guild
    embed = discord.Embed(title="Server Info", description="Details zum Server:", color=discord.Color.from_rgb(0, 0, 0))
    embed.add_field(name="Name", value=guild.name)
    embed.add_field(name="Mitgliederzahl", value=guild.member_count)
    embed.add_field(name="Erstellt am", value=guild.created_at.strftime("%d.%m.%Y"))
    await ctx.respond(embed=embed)

#-----------------------------------------------------------------------------------------------------------------------
                                         #--/clear--#

os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

@bot.slash_command(name="clear", description="Löscht Nachrichten und sendet ein Transcript als Embed")
async def clear(ctx: discord.ApplicationContext, amount: int):
    await ctx.defer(ephemeral=True)

    if not ctx.channel.permissions_for(ctx.author).manage_messages:
        await ctx.followup.send("🖤 Du hast keine Berechtigung, Nachrichten zu löschen.", ephemeral=True)
        return

    deleted = await ctx.channel.purge(limit=amount)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    transcript_data = {
        "channel": ctx.channel.name,
        "deleted_by": str(ctx.author),
        "timestamp": timestamp,
        "messages": []
    }

    for msg in deleted:
        transcript_data["messages"].append({
            "author": str(msg.author),
            "content": msg.content,
            "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    
    filename = f"{TRANSCRIPT_FOLDER}/{ctx.channel.name}_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)

   
    embed = discord.Embed(
        title="🧹 Nachrichten gelöscht",
        description=(
            f"**Channel:** {ctx.channel.mention}\n"
            f"**Gelöscht von:** {ctx.author.mention}\n"
            f"**Anzahl:** {len(deleted)} Nachrichten\n\n"
            f"🖤 Transcript gespeichert als:\n`{os.path.basename(filename)}`"
        ),
        color=discord.Color.from_rgb(0, 0, 0),
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text="Eclipse Bot • Löschprotokoll")

    
    log_channel = bot.get_channel(CLEAR_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=embed)
    else:
        await ctx.followup.send("🖤 Log-Channel wurde nicht gefunden.", ephemeral=True)
        return

    
    await ctx.followup.send(f"🖤 {len(deleted)} Nachrichten wurden gelöscht und protokolliert.", ephemeral=True)


#-----------------------------------------------------------------------------------------------------------------------
                                         #--/Userinfo--#

@bot.command(name='userinfo')
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
    embed = discord.Embed(title=f"Benutzerinfo: {member}", color=member.color, timestamp=datetime.datetime.utcnow())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Name", value=member.name, inline=True)
    embed.add_field(name="Spitzname", value=member.nick or "Keiner", inline=True)
    embed.add_field(name="Status", value=member.status, inline=True)
    embed.add_field(name="Beigetreten am", value=member.joined_at.strftime("%d.%m.%Y %H:%M:%S"), inline=True)
    embed.add_field(name="Account erstellt am", value=member.created_at.strftime("%d.%m.%Y %H:%M:%S"), inline=True)
    embed.add_field(name="Top-Rolle", value=member.top_role.mention, inline=True)
    embed.add_field(name="Rollen", value=", ".join(roles) if roles else "Keine", inline=False)
    embed.set_footer(text=f"Angefordert von {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

#-----------------------------------------------------------------------------------------------------------------------
                                         #--/Ban /unban--#

@bot.slash_command(name="ban", description="Bannt ein Mitglied vom Server")
async def ban(
    ctx: discord.ApplicationContext,
    member: discord.Member,
    reason: str = "Kein Grund angegeben"
):
    if not any(role.name == BAN_ROLE_NAME for role in ctx.author.roles):
        await ctx.respond("🖤 Du hast keine Berechtigung!", ephemeral=True)
        return

    try:
        try:
            dm_embed = discord.Embed(
                title="🖤 Du wurdest gebannt",
                description=(
                    f"Du wurdest von **{ctx.guild.name}** gebannt.\n\n"
                    f"**Grund:** {reason}\n\n"
                    "Falls du Fragen hast, wende dich bitte ans Moderationsteam."
                ),
                color=discord.Color.from_rgb(0, 0, 0)
            )
            await member.send(embed=dm_embed)
        except Exception:
            pass

        await ctx.guild.ban(user=member, reason=reason)

        embed = discord.Embed(
            title="🖤 Benutzer gebannt",
            description=f"{member.mention} wurde gebannt.",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        embed.add_field(name="Gebannt von", value=ctx.author.mention, inline=True)
        embed.add_field(name="Grund", value=reason, inline=False)
        embed.add_field(name="Benutzer-ID", value=str(member.id), inline=False)

        await ctx.respond(embed=embed, ephemeral=True)

        log_channel = discord.utils.get(ctx.guild.channels, name=BAN_CHANNEL_NAME)
        if log_channel:
            await log_channel.send(embed=embed)

    except Exception as e:
        await ctx.respond(f"🖤 Fehler: {str(e)}", ephemeral=True)



@bot.slash_command(name="unban", description="Entbannt einen Benutzer mit User-ID")
async def unban(
    ctx: discord.ApplicationContext,
    user_id: discord.Option(str, description="ID des Benutzers"),
    reason: str = "Kein Grund angegeben"
):
    if not any(role.name == MOD_ROLE_NAME for role in ctx.author.roles):
        await ctx.respond("🖤 Du hast keine Berechtigung!", ephemeral=True)
        return

    try:
        user = await bot.fetch_user(int(user_id))
        await ctx.guild.unban(user, reason=reason)

        embed = discord.Embed(
            title="🖤 Benutzer entbannt",
            description=f"{user.mention} wurde entbannt.",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        embed.add_field(name="Entbannt von", value=ctx.author.mention, inline=True)
        embed.add_field(name="Grund", value=reason, inline=False)

        await ctx.respond(embed=embed, ephemeral=True)

        log_channel = discord.utils.get(ctx.guild.channels, name=BAN_CHANNEL_NAME)
        if log_channel:
            await log_channel.send(embed=embed)

    except Exception as e:
        await ctx.respond(f"🖤 Fehler: {str(e)}", ephemeral=True)




#-----------------------------------------------------------------------------------------------------------------------
                                         #--/Slowmode--#

@bot.slash_command(name="slowmode", description="Setzt den Slowmode im aktuellen Channel (in Sekunden).")
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    if seconds < 0:
        await ctx.respond("🖤 Die Zeit kann nicht negativ sein.", ephemeral=True)
        return
    try:
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.respond(f"🖤 Slowmode wurde auf {seconds} Sekunden gesetzt.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"🖤 Fehler beim Setzen des Slowmodes: {e}",ephemeral = True)


#-----------------------------------------------------------------------------------------------------------------------
                                         #--/warn--#

@bot.slash_command(name="warn", description="Verwarnt einen User und loggt es im Log-Channel.")
async def warn(
    ctx: discord.ApplicationContext,
    member: discord.Member,
    grund: discord.Option(str, "Grund für die Verwarnung")
):
    
    if not any(role.name == WARN_ROLE_NAME for role in ctx.author.roles):
        await ctx.respond("🖤 Du hast keine Berechtigung, diesen Befehl zu nutzen!", ephemeral=True)
        return

    
    try:
        dm_embed = discord.Embed(
            title="🖤 Du wurdest verwarnt",
            description=f"Du wurdest auf **{ctx.guild.name}** verwarnt.\n\n**Grund:** {grund}",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        dm_embed.set_footer(text=f"Verwarnt von {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await member.send(embed=dm_embed)
    except Exception:
        pass

    
    embed = discord.Embed(
        title="🖤 Verwarnung",
        description=f"{member.mention} wurde verwarnt.",
        color=discord.Color.from_rgb(0, 0, 0),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="Grund", value=grund, inline=False)
    embed.add_field(name="Verwarnt von", value=ctx.author.mention, inline=True)
    embed.add_field(name="User-ID", value=str(member.id), inline=True)
    embed.set_footer(text=f"Eclipse Bot • Verwarnung")

    log_channel = bot.get_channel(WARN_LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=embed)

    await ctx.respond(f"{member.mention} wurde verwarnt und es wurde geloggt.", ephemeral=True)

#-----------------------------------------------------------------------------------------------------------------------
                                         #--/timeout /untimeout--#

@bot.slash_command(name="timeout", description="Timeout für ein Mitglied")
async def timeout(
    ctx: discord.ApplicationContext,
    member: discord.Member,
    duration: discord.Option(int, description="Timeout-Dauer in Minuten"),
    reason: str = "Kein Grund angegeben"
):
    if not any(role.name == MOD_ROLE_NAME for role in ctx.user.roles):
        await ctx.respond("⛔ Du hast keine Berechtigung!", ephemeral=True)
        return

    try:
        await member.timeout_for(timedelta(minutes=duration), reason=reason)

        embed = discord.Embed(
            title="⏳ Benutzer im Timeout",
            description=f"{member.mention} wurde für `{duration} Minuten` stummgeschaltet.",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        embed.add_field(name="Grund", value=reason, inline=False)
        embed.add_field(name="Timeout von", value=ctx.user.mention, inline=True)
        embed.add_field(name="Benutzer-ID", value=str(member.id), inline=False)

        await ctx.respond(embed=embed, ephemeral=True)

        log_channel = discord.utils.get(ctx.guild.channels, name=MUTE_CHANNEL_NAME)
        if log_channel:
            await log_channel.send(embed=embed)

    except Exception as e:
        await ctx.respond(f"❌ Fehler: {str(e)}", ephemeral=True)


@bot.slash_command(name="untimeout", description="Hebt den Timeout eines Benutzers auf")
async def untimeout(
    ctx: discord.ApplicationContext,
    member: discord.Member,
    reason: str = "Kein Grund angegeben"
):
    if not any(role.name == MOD_ROLE_NAME for role in ctx.user.roles):
        await ctx.respond("⛔ Du hast keine Berechtigung!", ephemeral=True)
        return

    try:
        await member.remove_timeout(reason=reason)

        embed = discord.Embed(
            title="🔊 Timeout aufgehoben",
            description=f"{member.mention} darf wieder sprechen.",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        embed.add_field(name="Grund", value=reason, inline=False)
        embed.add_field(name="Entmutet von", value=ctx.user.mention, inline=True)
        embed.add_field(name="Benutzer-ID", value=str(member.id), inline=False)

        await ctx.respond(embed=embed, ephemeral=True)

        log_channel = discord.utils.get(ctx.guild.channels, name=MUTE_CHANNEL_NAME)
        if log_channel:
            await log_channel.send(embed=embed)

    except Exception as e:
        await ctx.respond(f"❌ Fehler: {str(e)}", ephemeral=True)


#-----------------------------------------------------------------------------------------------------------------------
                                         #--/warnremove--#

@bot.slash_command(name="warnremove", description="Entfernt eine Verwarnung aus dem Log-Channel (nach User-ID).")
async def warnremove(
    ctx: discord.ApplicationContext,
    user_id: discord.Option(str, "User-ID der Verwarnung, die entfernt werden soll")
):
    if not any(role.name == WARN_ROLE_NAME for role in ctx.author.roles):
        await ctx.respond("⛔ Du hast keine Berechtigung, diesen Befehl zu nutzen!", ephemeral=True)
        return

    log_channel = bot.get_channel(WARN_LOG_CHANNEL_ID)
    if not log_channel:
        await ctx.respond("⚠️ Log-Channel nicht gefunden.", ephemeral=True)
        return

    deleted = False
    async for msg in log_channel.history(limit=100):
        if msg.embeds:
            embed = msg.embeds[0]
            for field in embed.fields:
                if field.name == "User-ID" and field.value == user_id:
                    await msg.delete()
                    await ctx.respond(f"✅ Verwarnung für User-ID `{user_id}` wurde entfernt.", ephemeral=True)
                    deleted = True
                    break
            if deleted:
                break

    if not deleted:
        await ctx.respond(f"⚠️ Keine Verwarnung mit User-ID `{user_id}` im Log gefunden.", ephemeral=True)


#-----------------------------------------------------------------------------------------------------------------------
                                         #--/embed--#

@bot.slash_command(
    name="embed",
    description="Erstellt einen Embed mit eigenen Angaben"
)
@option("titel", description="Der Titel des Embeds")
@option("beschreibung", description="Die Beschreibung")
@option("footer", description="Der Footer des Embeds")
@option("farbe", description="Hexfarbe (z. . #5865F2)", default="#5865F2")
async def embed_erstellen(
    ctx: discord.ApplicationContext,
    titel: str,
    beschreibung: str,
    footer: str,
    farbe: str
):

    try:
        farbwert = int(farbe.replace("#", ""), 16)
    except ValueError:
        await ctx.respond("🖤 Ungültige Farbe. Bitte im Format `#RRGGBB` angeben.", ephemeral=True)
        return

    embed = discord.Embed(
        title=titel,
        description=beschreibung,
        color=farbwert
    )
    embed.set_footer(text=footer)
    embed.set_thumbnail(url=THUMB_URL)
    embed.set_image(url=BANNER_URL)

    await ctx.respond(embed=embed)

#-----------------------------------------------------------------------------------------------------------------------
                                             






#-----------------------------------------------------------------------------------------------------------------------



load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")








bot.run(TOKEN)