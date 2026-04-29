# Discord Nickname + Role Bot for Fly.io

This bot watches one Discord channel. When a user sends a message there, it:

1. Sets their server nickname to the message content.
2. Assigns them a configured role.
3. Deletes their message.

## Required Discord bot permissions

The bot needs:

- Manage Nicknames
- Manage Roles
- Manage Messages
- View Channel
- Read Message History

The bot's role must be above the role it assigns and above users whose nicknames it changes.

## Required Discord developer portal intents

Enable these privileged gateway intents:

- Server Members Intent
- Message Content Intent

## Environment variables

Set these in Fly secrets:

```bash
fly secrets set DISCORD_TOKEN="your_bot_token"
fly secrets set TARGET_CHANNEL_ID="123456789012345678"
fly secrets set ROLE_ID="123456789012345678"
```

## Deploy

```bash
fly launch --no-deploy
fly deploy
```

If you already have an app, edit `fly.toml` and replace:

```toml
app = "your-discord-bot-name"
```

with your Fly app name.
