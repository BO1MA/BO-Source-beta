# Telegram Group Management Bot 🤖

Arabic-language Telegram group management bot built with Python.
Ported from a Lua-based bot (bian.lua / AVIRA.lua) to a clean Python architecture.

## Features

### 🛡️ Group Protection & Locks
- Lock/unlock 25+ content types (photos, videos, stickers, links, forwards, etc.)
- Configurable punishments per lock: delete, warn, kick, mute, ban
- Flood protection with configurable limits
- Arabic-only / English-only mode
- Long message filtering

### 👥 Role Hierarchy System
- 10-level role hierarchy (المطور الاساسي → العضو)
- Per-group and global role assignment
- Role-based command permissions
- Arabic role names with promote/demote commands

### 🔨 Moderation
- Ban / Unban (per-group and global)
- Mute / Unmute (per-group and global)
- Kick, Warn (with configurable max warnings)
- Reply-based targeting or by user ID

### 📢 Broadcasting
- Broadcast messages to all registered groups
- Broadcast with pin, forward, or text
- Per-group broadcast enable/disable

### 🎮 Games
- Emoji race (السمايلات) — first to send the emoji wins
- Number guessing (تخمين) — guess 1-10
- Letter game (الحروف) — find the different letter
- Leaderboard (الاسرع) — track fastest winners

### 🏷️ Tag All Members
- Tag all known members with mention links
- Rate-limited batching to avoid API limits

### 📌 Pin / Unpin
- Pin messages, unpin single or all

### ⚙️ Group Settings
- Toggle: Welcome, Farewell, Games, Tag, Broadcast, Force Subscribe, Protection
- Inline keyboard settings panel
- Custom welcome message with `{name}` placeholder
- Group rules

### 📝 Custom Commands & Replies
- Add per-group custom commands and auto-replies
- Add global commands/replies (sudo only)
- List and delete custom commands

### 🔔 Force Subscribe
- Require users to join a channel before interacting
- Configurable channel

### 🎬 YouTube Search & Download
- Search YouTube via Arabic command
- Download as MP3 or MP4 via inline buttons
- Uses yt-dlp

### 💬 Auto-Responses
- Arabic greeting responses (السلام عليكم, etc.)
- Fun insult command (اشتم)
- Text reversal (العكس)

### ℹ️ Info Commands
- User ID, Bio, Bot info, Group info
- Group link, Admin list, Statistics
- Developer info

## Setup

### Prerequisites
- Python 3.10+
- Redis server running on localhost:6379
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- (Optional) yt-dlp for YouTube features

### Installation

```bash
# Clone and enter the project
cd telegram-bot

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your bot token, sudo ID, etc.

# Run the bot
python -m src.bot
```

### Configuration (.env)

```env
BOT_TOKEN=your_bot_token_here
SUDO_ID=your_telegram_user_id
SUDO_USERNAME=your_username
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
CHANNEL_USERNAME=@your_channel
CHANNEL_ID=-100xxxxxxxxxx
```

## Project Structure

```
telegram-bot/
├── src/
│   ├── bot.py              # Main entry point
│   ├── config.py            # Environment config
│   ├── constants/           # Roles, messages, commands
│   ├── handlers/            # All command handlers
│   │   ├── start.py         # /start, welcome, farewell, info
│   │   ├── admin.py         # Role management
│   │   ├── moderation.py    # Ban, mute, kick, warn
│   │   ├── broadcast.py     # Broadcasting
│   │   ├── games.py         # Games
│   │   ├── tag.py           # Tag all members
│   │   ├── locks.py         # Content locks
│   │   ├── permissions.py   # Settings toggles
│   │   └── youtube.py       # YouTube download
│   ├── models/              # User, Group dataclasses
│   ├── services/            # Redis, User, Group services
│   └── utils/               # Decorators, keyboards, helpers
├── data/commands.json
├── tests/
├── .env.example
├── requirements.txt
└── setup.py
```

## Running Tests

```bash
python -m pytest tests/
```

## License

MIT
