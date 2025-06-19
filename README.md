# Discord Role Bot

Discord Role Bot automates developer onboarding on a Discord server. It posts a
persistent message with interactive buttons and dropdowns to gather information
and assign appropriate roles. Profile data is stored locally in an SQLite
database.

## Features

- Interactive onboarding message for developers
- Collects GitHub and X/Twitter handles
- Assigns primary, sub, and ecosystem roles
- Optional hackathon role menu for event participants

## Setup

1. Install Python 3.10 or later.
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and define the environment variables
   described below.

### Environment Variables

- `BOT_TOKEN` – token for your Discord bot
- `GUILD_ID` – numerical ID of the Discord server where the bot will operate
- `CHANNEL_ID` – numerical ID of the channel where the onboarding message should
  be sent

## Customizing Roles

Some role and channel IDs are hard-coded in `bot.py`. Replace them with your own
IDs so the bot can assign the correct roles and link to the right channels.

### Hackathon Roles

In the `HackathonRoleDropdown` class you will find role IDs and the associated
channel IDs:

```python
class HackathonRoleDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="AMM Hackathon", value="1348368518311051384"),
            discord.SelectOption(label="MLH (Major League Hacking)", value="1329454653217177660"),
        ]
        super().__init__(placeholder="Select your hackathon role...", options=options)
```

Further down in the same class, update the mapping from role ID to channel ID so
users are directed to the correct channel after receiving a role. To obtain IDs,
enable **Developer Mode** in Discord, then right-click any role or channel and
select **Copy ID**.

## Running the Bot

After setting up the environment variables and customizing IDs, start the bot with:

```bash
python bot.py
```

When the bot starts it will post the onboarding message in the specified channel
and handle role assignment for new developers.

## Database

Profile data is stored in `developer_profiles.db` in the project directory. The
database is created automatically if it does not exist.

