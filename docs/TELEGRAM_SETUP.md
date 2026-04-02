# Telegram Bot Setup Guide

This guide will help you connect SemiShape to your Telegram account.

## Step 1: Create a Telegram Bot

1. Open Telegram on your phone or desktop
2. Search for **@BotFather** (official Telegram bot)
3. Send the command: `/newbot`
4. Follow the instructions:
   - Choose a name (e.g., "SemiShape CAD")
   - Choose a username (must end with `bot`, e.g., `semishape_cad_bot`)
5. **Copy the API Token** (looks like `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Add Token to Agent Zero

### Option A: Add to secrets.env
```bash
echo 'TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz' >> /a0/usr/projects/semishape/.a0proj/secrets.env
```

### Option B: Add to main .env
```bash
echo 'TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz' >> /a0/usr/.env
```

## Step 3: Install Dependencies

```bash
cd /a0/usr/projects/semishape
source venv/bin/activate
pip install python-telegram-bot
```

## Step 4: Run the Bot

```bash
python -m telegram.telegram_bot
```

## Step 5: Test the Bot

1. Open Telegram
2. Search for your bot by username
3. Send `/start`
4. Try: "Vytvoř kvádr 50x30x10mm"

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help |
| `/gen <description>` | Generate model |
| `/cs` | Switch to Czech |
| `/en` | Switch to English |

## Example Usage

```
User: Vytvoř válec o průměru 50mm a výšce 100mm
Bot: [generates code and sends STL file]
```

## Troubleshooting

### Bot not responding?
- Check if the token is correct
- Check if python-telegram-bot is installed
- Check logs for errors

### API Key issues?
- Verify OPENROUTER API key in /a0/usr/.env
- Test with: `python -m src.cli generate "test"`

## Security Note

- Never share your bot token
- The token is stored locally in your Agent Zero environment
- Only you can access your bot
