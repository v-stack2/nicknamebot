# Discord Nickname + Role Bot for Fly.io

This bot watches one Discord channel. When a user sends a message there, it:

1. Sets their server nickname to the message content.
2. Assigns them a configured role.
3. Deletes their message.

## Fly secrets

```bash
fly secrets set DISCORD_TOKEN="your_bot_token"
fly secrets set TARGET_CHANNEL_ID="123456789012345678"
fly secrets set ROLE_ID="123456789012345678"
```

## Discord Developer Portal

Enable:

- Server Members Intent
- Message Content Intent

## Discord server permissions

The bot role needs:

- View Channel
- Read Message History
- Manage Messages
- Manage Nicknames
- Manage Roles

The bot role must be higher than the role it assigns and higher than users whose nicknames it edits.

## Deploy

Make sure `app = "nicknamebot"` in `fly.toml` matches your actual Fly app name.

```bash
fly deploy
fly machines restart
fly logs
```
