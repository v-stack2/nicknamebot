import logging
import os
import re

import discord
from discord.ext import commands


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

def required_int_env(name: str) -> int:
    raw = os.getenv(name)
    if not raw:
        raise RuntimeError(f"Missing {name} environment variable.")
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a Discord numeric ID, got: {raw!r}") from exc


TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN environment variable.")

TARGET_CHANNEL_ID = required_int_env("TARGET_CHANNEL_ID")
ROLE_ID = required_int_env("ROLE_ID")
DELETE_MESSAGES = os.getenv("DELETE_MESSAGES", "true").lower() == "true"
BOT_DEBUG = os.getenv("BOT_DEBUG", "false").lower() == "true"


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
async def on_ready() -> None:
    logging.info("Logged in as %s (%s)", bot.user, bot.user.id)
    logging.info("Watching TARGET_CHANNEL_ID=%s and assigning ROLE_ID=%s", TARGET_CHANNEL_ID, ROLE_ID)


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    if BOT_DEBUG:
        logging.info(
            "Message seen: guild=%s channel=%s author=%s content_length=%s",
            getattr(message.guild, "id", None),
            message.channel.id,
            message.author.id,
            len(message.content or ""),
        )

    if message.guild is None:
        return

    if message.channel.id != TARGET_CHANNEL_ID:
        return

    guild = message.guild
    nickname = clean_nickname(message.content or "")

    if not nickname:
        logging.info("Empty nickname submitted by user=%s", message.author.id)
        if DELETE_MESSAGES:
            try:
                await message.delete()
            except discord.Forbidden:
                logging.exception("Cannot delete empty submission: missing Manage Messages or channel override denies it.")
            except discord.HTTPException:
                logging.exception("HTTP error while deleting empty submission.")
        return

    role = guild.get_role(ROLE_ID)
    if role is None:
        logging.error("Role not found. ROLE_ID=%s is not a role in guild=%s", ROLE_ID, guild.id)
        return

    try:
        member = guild.get_member(message.author.id)
        if member is None:
            member = await guild.fetch_member(message.author.id)
    except discord.HTTPException:
        logging.exception("Could not resolve member object for user=%s", message.author.id)
        return

    try:
        await member.edit(nick=nickname, reason="Nickname submitted through registration channel")
        logging.info("Nickname set for user=%s to %r", member.id, nickname)
    except discord.Forbidden:
        logging.exception(
            "Cannot change nickname for user=%s. Check Manage Nicknames and bot role hierarchy.",
            member.id,
        )
    except discord.HTTPException:
        logging.exception("HTTP error while changing nickname for user=%s", member.id)

    try:
        await member.add_roles(role, reason="Submitted nickname through registration channel")
        logging.info("Role %s assigned to user=%s", role.id, member.id)
    except discord.Forbidden:
        logging.exception(
            "Cannot assign role=%s to user=%s. Check Manage Roles, role hierarchy, and that the target role is below the bot role.",
            role.id,
            member.id,
        )
    except discord.HTTPException:
        logging.exception("HTTP error while assigning role=%s to user=%s", role.id, member.id)

    if DELETE_MESSAGES:
        try:
            await message.delete()
            logging.info("Deleted submission message=%s from user=%s", message.id, member.id)
        except discord.Forbidden:
            logging.exception("Cannot delete message. Check Manage Messages and channel overrides.")
        except discord.HTTPException:
            logging.exception("HTTP error while deleting message=%s", message.id)


bot.run(TOKEN)
