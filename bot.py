import os
import re
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "0"))
ROLE_ID = int(os.getenv("ROLE_ID", "0"))
DELETE_MESSAGES = os.getenv("DELETE_MESSAGES", "true").lower() == "true"

if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN environment variable.")
if not TARGET_CHANNEL_ID:
    raise RuntimeError("Missing TARGET_CHANNEL_ID environment variable.")
if not ROLE_ID:
    raise RuntimeError("Missing ROLE_ID environment variable.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def clean_nickname(text: str) -> str:
    """Make user-submitted nickname safe enough for Discord."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("@everyone", "everyone").replace("@here", "here")
    return text[:32]


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != TARGET_CHANNEL_ID:
        return

    guild = message.guild
    if guild is None:
        return

    member = message.author
    nickname = clean_nickname(message.content)

    if not nickname:
        if DELETE_MESSAGES:
            try:
                await message.delete()
            except discord.Forbidden:
                print("Missing permission: Manage Messages")
        return

    role = guild.get_role(ROLE_ID)
    if role is None:
        print("Role not found. Check ROLE_ID.")
        return

    try:
        await member.edit(nick=nickname, reason="Nickname submitted through registration channel")
    except discord.Forbidden:
        print(f"Cannot change nickname for {member}. Bot role may be too low or missing Manage Nicknames.")
    except discord.HTTPException as e:
        print(f"Nickname update failed: {e}")

    try:
        await member.add_roles(role, reason="Submitted nickname through registration channel")
    except discord.Forbidden:
        print("Cannot assign role. Bot role may be too low or missing Manage Roles.")
    except discord.HTTPException as e:
        print(f"Role assignment failed: {e}")

    if DELETE_MESSAGES:
        try:
            await message.delete()
        except discord.Forbidden:
            print("Cannot delete message. Missing Manage Messages.")
        except discord.HTTPException as e:
            print(f"Message delete failed: {e}")

    await bot.process_commands(message)


bot.run(TOKEN)
