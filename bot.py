import os
import re
import logging

import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nicknamebot")

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
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("@everyone", "everyone").replace("@here", "here")
    return text[:32]


@bot.event
async def on_ready():
    log.info("Logged in as %s (%s)", bot.user, bot.user.id)
    log.info("Watching channel ID: %s", TARGET_CHANNEL_ID)
    log.info("Assigning role ID: %s", ROLE_ID)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.guild is None:
        return

    if message.channel.id != TARGET_CHANNEL_ID:
        return

    member = message.author
    nickname = clean_nickname(message.content)

    log.info(
        "Received registration message from %s (%s) in channel %s: %r",
        member,
        member.id,
        message.channel.id,
        message.content,
    )

    if not nickname:
        log.info("Empty nickname after cleaning; deleting only.")
        if DELETE_MESSAGES:
            try:
                await message.delete()
            except Exception as e:
                log.exception("Failed to delete empty message: %s", e)
        return

    role = message.guild.get_role(ROLE_ID)
    if role is None:
        log.error("Role not found. ROLE_ID=%s is wrong or from another server.", ROLE_ID)
        return

    try:
        await member.edit(nick=nickname, reason="Nickname submitted through registration channel")
        log.info("Changed nickname for %s to %r", member.id, nickname)
    except discord.Forbidden:
        log.exception("Cannot change nickname. Check Manage Nicknames and bot role hierarchy.")
    except discord.HTTPException as e:
        log.exception("Nickname update failed: %s", e)

    try:
        await member.add_roles(role, reason="Submitted nickname through registration channel")
        log.info("Assigned role %s to %s", role.id, member.id)
    except discord.Forbidden:
        log.exception("Cannot assign role. Check Manage Roles and bot role hierarchy above assigned role.")
    except discord.HTTPException as e:
        log.exception("Role assignment failed: %s", e)

    if DELETE_MESSAGES:
        try:
            await message.delete()
            log.info("Deleted registration message from %s", member.id)
        except discord.Forbidden:
            log.exception("Cannot delete message. Check Manage Messages in this channel.")
        except discord.HTTPException as e:
            log.exception("Message delete failed: %s", e)

    await bot.process_commands(message)


bot.run(TOKEN)
