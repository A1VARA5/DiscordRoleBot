# Discord Role Bot

Discord Role Bot automates developer onboarding on a Discord server. It posts a persistent message with interactive buttons and dropdowns to gather information and assign appropriate roles. The bot stores profile data in a local SQLite database.

## Setup

1. Install Python 3.10 or later.
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and define the environment variables described below.

### Environment Variables

- `BOT_TOKEN` – token for your Discord bot.
- `GUILD_ID` – numerical ID of the Discord server where the bot will operate.
- `CHANNEL_ID` – numerical ID of the channel where the onboarding message should be sent.

## Running the Bot

After setting up the environment variables, start the bot with:

```bash
python bot.py
```

When the bot starts it will post an onboarding message in the specified channel and handle role assignment for new developers.
