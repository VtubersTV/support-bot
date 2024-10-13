import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from utils import is_staff, check_for_ffmpeg
import requests
from lofi import LofiMusicPlayer, YTDLSource
import sqlite3
from db import db_start


# Load environment variables from a .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GITHUB_SECRET = os.getenv("GITHUB_SECRET")
db_connection = sqlite3.connect("bot.sqlite")

cursor = db_connection.cursor()

# Configure the bot's intents and command prefix
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

activity = discord.Activity(
    name="VTubers on vtubers.tv", type=discord.ActivityType.watching
)
bot = commands.Bot(command_prefix="!", intents=intents, activity=activity)

lofi_music_player = LofiMusicPlayer(bot)

SITE_URLS = {
    "frontend": "https://vtubers.tv",
    "api": "https://api.vtubers.tv/health",
    "documentation": "https://docs.vtubers.tv",
}


@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    print(f"Logged in as {bot.user} ({bot.user.id})")
    print("------")
    await lofi_music_player.connect(cursor)


@bot.event
async def on_member_join(member: discord.Member):
    """Event triggered when a new member joins the server."""
    role = member.guild.get_role(1294829099461902397)
    if role:
        await member.add_roles(role)
        print(f"Assigned role {role.name} to {member.name}")
    else:
        print(f"Role not found for {member.name}")


@bot.command(name="nuke")
async def nuke(ctx: commands.Context, limit: int = 100):
    """Deletes all messages in the current channel."""
    if is_staff(ctx.author):
        await ctx.reply(f"Nuking {limit} messages... (Waiting 5 seconds before nuking)")
        await asyncio.sleep(5)
        await ctx.channel.purge(limit=limit)
    else:
        await ctx.reply("You do not have permission to use this command. :no_entry:")


@bot.command(name="ping")
async def ping(ctx: commands.Context):
    """Get the server latency."""

    msg = await ctx.reply("Please wait...")
    embed = discord.Embed(title="Server Status", color=0x00FF00)
    embed.add_field(
        name="Discord API Latency", value=f"{round(bot.latency * 1000)}ms", inline=False
    )

    for name, url in SITE_URLS.items():
        response = requests.get(url)
        status = "✅" if response.ok else "❌"
        embed.add_field(
            name=name.capitalize(),
            value=f"{status} {url} ({response.status_code})",
            inline=False,
        )

    await msg.edit(content=None, embed=embed)


@bot.command(name="serverinfo")
async def server_info(ctx: commands.Context):
    """Displays information about the server."""
    guild = ctx.guild
    embed = discord.Embed(title=f"Server Information - {guild.name}", color=0x3498DB)
    embed.add_field(name="Member Count", value=guild.member_count, inline=True)
    embed.add_field(name="Role Count", value=len(guild.roles), inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.set_thumbnail(url=guild.icon.url)

    await ctx.reply(embed=embed)

@bot.command(name="add-lofi")
async def add_lofi(ctx: commands.Context, url: str):
    """Add a Lofi music stream to the database."""
    if is_staff(ctx.author):
        if not url.startswith("https://www.youtube.com/watch?v="):
            await ctx.reply("Invalid URL. Please provide a valid YouTube URL.")
            return
        
        data = await YTDLSource.get_info(url)

        cursor.execute("SELECT video_id FROM LofiMusic WHERE video_id = ?", (data["id"],))
        existing_entry = cursor.fetchone()

        if existing_entry:
            await ctx.reply("This video is already in the database.")
            return

        msg = await ctx.reply("Downloading to stop rate limiting... Please wait.")
        file_name = await YTDLSource.download(url)
        
        if not file_name:
            await msg.edit(content="Download failed. Please try again.")
            return
        
        await msg.edit(content="Downloaded. Adding to database... Please wait.")
        cursor.execute("INSERT INTO LofiMusic (title, filename, thumbnail, duration, added_by, video_id) VALUES (?, ?, ?, ?, ?, ?)",
                       (data["title"], file_name, data["thumbnail"], data["duration"], ctx.author.id, data["id"]))
        db_connection.commit()
        await msg.edit(content="Added to database.")
    else:
        await ctx.reply("You do not have permission to use this command. :no_entry:")

@bot.command(name="lofi")
async def play_lofi(ctx: commands.Context, id: str = None):
    """Get lofi music from the database"""

    def format_duration(duration):
        return str(int(duration / 60)) + ":" + str(duration % 60).zfill(2)
        

    if id is None:
        data = cursor.execute("SELECT * FROM LofiMusic")

        embed = discord.Embed(title="Lofi Music", color=0x3498DB)
        for row in data:
            embed.add_field(name=row[1], value=row[3], inline=False)
        await ctx.reply(embed=embed)
    else:
        data = cursor.execute("SELECT * FROM LofiMusic WHERE video_id = ?", (id,))
        row = data.fetchone()
        if row is None:
            await ctx.reply("No entry found with that ID.")
            return
        
        embed = discord.Embed(title=row[1], color=0x3498DB)
        embed.url = f"https://www.youtube.com/watch?v={row[3]}"
        embed.add_field(name="Duration", value=format_duration(row[5]), inline=False)
        embed.set_image(url=row[4])
        await ctx.reply(embed=embed)

@bot.event
async def on_message(message: discord.Message):
    """Handles new messages and manages slowmode based on predicted activity."""
    if message.author.bot:
        return
    await bot.process_commands(message)


if __name__ == "__main__":
    if TOKEN:
        check_for_ffmpeg()
        db_start(cursor)
        print("Starting bot...")
        bot.run(TOKEN)
    else:
        print("Bot token not found. Make sure it's set in the .env file.")
