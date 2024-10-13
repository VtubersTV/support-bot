import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from utils import is_staff
import requests

# Load environment variables from a .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GITHUB_SECRET = os.getenv("GITHUB_SECRET")

# Configure the bot's intents and command prefix
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

activity = discord.Activity(
    name="VTubers on vtubers.tv", type=discord.ActivityType.watching
)
bot = commands.Bot(command_prefix="!", intents=intents, activity=activity)

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


@bot.event
async def on_message(message: discord.Message):
    """Handles new messages and manages slowmode based on predicted activity."""
    if message.author.bot:
        return
    await bot.process_commands(message)


if __name__ == "__main__":
    if TOKEN:
        print("Starting bot...")
        bot.run(TOKEN)
    else:
        print("Bot token not found. Make sure it's set in the .env file.")
