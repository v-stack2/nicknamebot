print("BOOT: bot.py file started", flush=True)

import logging
import os
import re
import sys

import discord
from discord.ext import commands


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
    force=True,
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
BOT_DEBUG = os.getenv("BOT_DEBUG", "true").lower() == "true"

print(f"BOOT: loaded config TARGET_CHANNEL_ID={TARGET_CHANNEL_ID} ROLE_ID={ROLE_ID}", flush=True)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


def clean_nickname(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("@everyone", "everyone").replace("@here", "here")
    return text[:32]


@bot.event
async def on_ready() -> None:
    logging.info("READY: logged in as %s (%s)", bot.user, bot.user.id)
    logging.info("CONFIG: TARGET_CHANNEL_ID=%s ROLE_ID=%s", TARGET_CHANNEL_ID, ROLE_ID)

    for guild in bot.guilds:
        channel = guild.get_channel(TARGET_CHANNEL_ID)
        role = guild.get_role(ROLE_ID)

        logging.info("CHECK: guild=%s (%s)", guild.name, guild.id)
        logging.info("CHECK: target channel=%s", f"{channel.name} ({channel.id})" if channel else "NOT FOUND")
        logging.info("CHECK: role=%s", f"{role.name} ({role.id})" if role else "NOT FOUND")

        me = guild.me
        if me:
            logging.info("CHECK: bot top role=%s position=%s", me.top_role.name, me.top_role.position)
            if role:
                logging.info("CHECK: assigned role position=%s", role.position)


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    logging.info(
        "MESSAGE: guild=%s channel=%s author=%s content=%r",
        getattr(message.guild, "id", None),
        message.channel.id,
        message.author.id,
        message.content,
    )

    if message.guild is None:
        logging.info("SKIP: DM message")
        return

    if message.channel.id != TARGET_CHANNEL_ID:
        logging.info("SKIP: wrong channel. got=%s expected=%s", message.channel.id, TARGET_CHANNEL_ID)
        return

    guild = message.guild
    nickname = clean_nickname(message.content or "")

    if not nickname:
        logging.info("SKIP: empty nickname from user=%s", message.author.id)

        if DELETE_MESSAGES:
            try:
                await message.delete()
                logging.info("DELETE: empty message deleted")
            except Exception:
                logging.exception("DELETE FAILED: empty message")

        return

    role = guild.get_role(ROLE_ID)
    if role is None:
        logging.error("ROLE FAILED: ROLE_ID=%s not found in guild=%s", ROLE_ID, guild.id)
        return

    try:
        member = guild.get_member(message.author.id)
        if member is None:
            logging.info("MEMBER: cache miss, fetching member=%s", message.author.id)
            member = await guild.fetch_member(message.author.id)
    except Exception:
        logging.exception("MEMBER FAILED: could not resolve member=%s", message.author.id)
        return

    try:
        await member.edit(nick=nickname, reason="Nickname submitted through registration channel")
        logging.info("NICK OK: user=%s nickname=%r", member.id, nickname)
    except Exception:
        logging.exception("NICK FAILED: user=%s", member.id)

    try:
        await member.add_roles(role, reason="Submitted nickname through registration channel")
        logging.info("ROLE OK: role=%s user=%s", role.id, member.id)
    except Exception:
        logging.exception("ROLE FAILED: role=%s user=%s", role.id, member.id)

    if DELETE_MESSAGES:
        try:
            await message.delete()
            logging.info("DELETE OK: message=%s user=%s", message.id, member.id)
        except Exception:
            logging.exception("DELETE FAILED: message=%s", message.id)


print("BOOT: calling bot.run()", flush=True)
bot.run(TOKEN)
