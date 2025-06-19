import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
import aiosqlite
import pandas as pd
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Database Setup
async def init_db():
    global db
    db = await aiosqlite.connect("developer_profiles.db")
    cursor = await db.cursor()
    await cursor.execute("""
    CREATE TABLE IF NOT EXISTS developers (
        user_id TEXT PRIMARY KEY,
        primary_role TEXT,
        sub_roles TEXT,
        github TEXT,
        twitter TEXT,
        agreed_to_terms INTEGER,
        ecosystems TEXT
    )
    """)
    await db.commit()

# Bot Initialization
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Persistent Introductory Message
@bot.event
async def on_ready():
    await init_db()
    try:
        logger.info("[LOG] Bot is starting...")
        guild = discord.utils.get(bot.guilds, id=GUILD_ID)
        if guild is None:
            logger.error(f"[ERROR] Guild with ID {GUILD_ID} not found.")
            return

        channel = guild.get_channel(CHANNEL_ID)
        if channel is None:
            logger.error(f"[ERROR] Channel with ID {CHANNEL_ID} not found.")
            return

        embed = discord.Embed(
            title="🔑 Developer Onboarding",
            description=(
                "**This onboarding process is intended for developers and those interested in becoming block producers who wish to unlock additional channels and resources within the Midnight ecosystem.**\n\n"
                "If you're interested in:\n"
                "• **Participating in zk discussions or testnet activities**\n"
                "• **Accessing technical resources and development tools**\n"
                "• **Exploring opportunities to become a block producer**\n"
                "• **Engaging in developer-focused conversations and collaborations**\n"
                "\n"
                "Then this onboarding is for you!\n"
                "⚠️ **Note:** If you're here for general community interaction or non-technical discussions, the **VERIFIED** role you’ve already acquired is sufficient and grants you access to the main community spaces. No further action is needed in that case.\n"
                "\n"
                "📋 **Developers and block producers**, to continue and unlock these resources, please click the button below to start your onboarding process."
            ),
            color=discord.Color.from_str("#0A0A0A")
        )
        embed.set_footer(text="For questions or assistance, reach out to a moderator.")

        view = View()
        view.add_item(Button(label="Start Developer Setup", style=discord.ButtonStyle.primary, custom_id="start_setup"))
        view.add_item(Button(label="Get Hackathon Role", style=discord.ButtonStyle.secondary, custom_id="get_hackathon_role"))

        await channel.send(embed=embed, view=view)
        logger.info(f"[LOG] Bot is ready and message sent to channel ID {CHANNEL_ID}.")
    except Exception as e:
        logger.error(f"[ERROR] An exception occurred during startup: {e}")

# Assign Roles (Including Ecosystem Roles)
async def assign_roles(user: discord.Member):
    async with db.execute("SELECT primary_role, sub_roles, ecosystems FROM developers WHERE user_id = ?", (str(user.id),)) as cursor:
        data = await cursor.fetchone()
    if not data:
        logger.info(f"[LOG] No data found for user {user}.")
        return

    primary_role, sub_roles, ecosystems = data
    guild = user.guild
    roles_to_assign = []

    # Assign the primary role
    if primary_role:
        primary_role_obj = discord.utils.get(guild.roles, name=primary_role)
        if primary_role_obj:
            roles_to_assign.append(primary_role_obj)
        else:
            logger.info(f"[LOG] Primary role '{primary_role}' not found in the server!")

    # Assign sub-roles
    if sub_roles:
        for sub_role in sub_roles.split(", "):
            sub_role_obj = discord.utils.get(guild.roles, name=sub_role)
            if sub_role_obj:
                roles_to_assign.append(sub_role_obj)
            else:
                logger.info(f"[LOG] Sub-role '{sub_role}' not found in the server!")

    # Assign ecosystem roles
    if ecosystems:
        for ecosystem in ecosystems.split(", "):
            ecosystem_role = discord.utils.get(guild.roles, name=ecosystem)
            if ecosystem_role:
                roles_to_assign.append(ecosystem_role)
            else:
                logger.info(f"[LOG] Ecosystem role '{ecosystem}' not found in the server!")

    # Add all roles to the user
    if roles_to_assign:
        try:
            await user.add_roles(*roles_to_assign)
            logger.info(f"[LOG] Assigned roles to {user}: {', '.join([role.name for role in roles_to_assign])}")
        except discord.Forbidden:
            logger.error(f"[ERROR] Bot lacks permission to assign roles.")
        except discord.HTTPException as e:
            logger.error(f"[ERROR] Failed to assign roles due to an HTTP error: {e}")
    else:
        logger.info(f"[LOG] No roles were assigned to {user}.")

# Dropdowns
class PrimaryRoleDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Block Producer", value="Block Producer"),
            discord.SelectOption(label="Dapp Developer", value="Dapp Developer"),
            discord.SelectOption(label="Contributor", value="Contributor"),
            discord.SelectOption(label="Zkp Developer", value="Zkp Developer"),
            discord.SelectOption(label="Beginner", value="Beginner"),
            discord.SelectOption(label="MLH (Major League Hacking Member)", value="MLH")  # Use "MLH" as the role name
        ]
        super().__init__(placeholder="Select your primary role...", options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        primary_role = self.values[0]  # Get the correct role name from the value
        await db.execute("INSERT OR REPLACE INTO developers (user_id, primary_role) VALUES (?, ?)", (user_id, primary_role))
        await db.commit()
        logger.info(f"[LOG] User {interaction.user} selected primary role: {primary_role}")

        embed = discord.Embed(
            title="Primary Role Selected",
            description=f"Your primary role is: **{primary_role}**.\n\nClick **Next** to select additional roles.",
            color=discord.Color.from_str("#0A0A0A")
        )
        view = View()
        view.add_item(Button(label="Next", style=discord.ButtonStyle.primary, custom_id="select_sub_roles"))
        await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

class SubRoleDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Frontend Developer"),
            discord.SelectOption(label="Backend Developer"),
            discord.SelectOption(label="Full-Stack Developer"),
            discord.SelectOption(label="Blockchain Developer"),
            discord.SelectOption(label="DevOps Engineer"),
            discord.SelectOption(label="Smart Contract Developer"),
            discord.SelectOption(label="Data Scientist / AI Engineer"),
            discord.SelectOption(label="Cardano SPO")
        ]
        super().__init__(placeholder="Select your sub-roles (optional)...", options=options, max_values=len(options))

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        sub_roles = ", ".join(self.values)
        await db.execute("UPDATE developers SET sub_roles = ? WHERE user_id = ?", (sub_roles, user_id))
        await db.commit()
        logger.info(f"[LOG] User {interaction.user} selected sub-roles: {sub_roles}")

        embed = discord.Embed(
            title="Sub-Roles Selected",
            description=f"You selected the following sub-roles: **{sub_roles}**.\n\nClick **Next** to select your ecosystem.",
            color=discord.Color.from_str("#0A0A0A")
        )
        view = View()
        view.add_item(Button(label="Next", style=discord.ButtonStyle.primary, custom_id="select_ecosystems"))
        await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

class EcosystemDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Cardano"),
            discord.SelectOption(label="Ethereum"),
            discord.SelectOption(label="Solana"),
            discord.SelectOption(label="Bitcoin"),
            discord.SelectOption(label="Polygon"),
            discord.SelectOption(label="Binance Smart Chain"),
            discord.SelectOption(label="XRP"),
            discord.SelectOption(label="Avalanche")
        ]
        super().__init__(placeholder="Select your ecosystems (you can choose multiple)...", options=options, max_values=len(options))

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        ecosystems = ", ".join(self.values)
        await db.execute("UPDATE developers SET ecosystems = ? WHERE user_id = ?", (ecosystems, user_id))
        await db.commit()
        logger.info(f"[LOG] User {interaction.user} selected ecosystems: {ecosystems}")

        embed = discord.Embed(
            title="Ecosystems Selected",
            description=f"You selected: **{ecosystems}**.\n\nClick **Next** to provide your GitHub and X profiles.",
            color=discord.Color.from_str("#0A0A0A")
        )
        view = View()
        view.add_item(Button(label="Next", style=discord.ButtonStyle.primary, custom_id="provide_profiles"))
        await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

class ProfileLinksModal(Modal):
    def __init__(self):
        super().__init__(title="Submit Your Profiles")
        self.github = TextInput(label="GitHub Link", placeholder="https://github.com/yourusername", required=True)
        self.twitter = TextInput(label="X Profile Link", placeholder="https://x.com/yourusername", required=True)
        self.add_item(self.github)
        self.add_item(self.twitter)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        github = self.github.value.strip()
        twitter = self.twitter.value.strip()

        async with db.execute("SELECT user_id FROM developers WHERE github = ? OR twitter = ?", (github, twitter)) as cursor:
            if await cursor.fetchone():
                await interaction.response.send_message(
                    "This GitHub or X profile is already in use. Please contact the Community Manager.",
                    ephemeral=True
                )
                return

        await db.execute("UPDATE developers SET github = ?, twitter = ? WHERE user_id = ?", (github, twitter, user_id))
        await db.commit()
        logger.info(f"[LOG] User {interaction.user} submitted profiles: GitHub={github}, X={twitter}")

        embed = discord.Embed(
            title="Profiles Submitted",
            description="Your GitHub and X profiles have been saved. Click **Next** to agree to the terms.",
            color=discord.Color.from_str("#0A0A0A")
        )
        view = View()
        view.add_item(Button(label="Next", style=discord.ButtonStyle.primary, custom_id="agree_terms"))
        await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

class AgreementModal(Modal):
    def __init__(self):
        super().__init__(title="Agree to the Terms")
        self.agree_input = TextInput(
            label="Type 'I Agree'",
            placeholder="Type 'I Agree' to confirm",
            required=True,
            max_length=20
        )
        self.add_item(self.agree_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        if self.agree_input.value.strip().lower() != "i agree":
            await interaction.response.send_message(
                "You must type 'I Agree' exactly to proceed.",
                ephemeral=True
            )
            return

        # Mark the user as agreeing to the terms
        await db.execute("UPDATE developers SET agreed_to_terms = 1 WHERE user_id = ?", (user_id,))
        await db.commit()
        logger.info(f"[LOG] User {interaction.user} agreed to the terms.")

        # Send completion message first
        embed = discord.Embed(
            title="Setup Complete!",
            description="🎉 Thank you for completing the developer setup. Your roles are being assigned now!",
            color=discord.Color.from_str("#0A0A0A")
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Assign roles to the user after the message
        await assign_roles(interaction.user)

# Hackathon Role Dropdown
class HackathonRoleDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="AMM Hackathon", value="1348368518311051384"),  # Updated Role
            discord.SelectOption(label="MLH (Major League Hacking)", value="1329454653217177660")
        ]
        super().__init__(placeholder="Select your hackathon role...", options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        selected_role_id = int(self.values[0])
        guild = interaction.guild
        role = guild.get_role(selected_role_id)

        if role in interaction.user.roles:
            await interaction.response.send_message(
                f"You already have the role: **{role.name}**.",
                ephemeral=True
            )
            return

        try:
            await interaction.user.add_roles(role)
            print(f"[LOG] Assigned hackathon role {role.name} to {interaction.user}")

            # Define the associated channel ID for the role
            channel_id = (
                1348368328099495946 if selected_role_id == 1348368518311051384  # AMM Hackathon Channel ID
                else 1329450380584550482 if selected_role_id == 1329454653217177660  # MLH Hackathon Channel ID
                else None
            )

            if channel_id:
                channel = guild.get_channel(channel_id)
                if channel:
                    await interaction.response.send_message(
                        f"✅ Role **{role.name}** assigned successfully!\n"
                        f"🔗 You can now access the channel: {channel.mention}",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"✅ Role **{role.name}** assigned successfully, but I couldn't find the channel.",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    f"✅ Role **{role.name}** assigned successfully!",
                    ephemeral=True
                )

        except discord.Forbidden:
            await interaction.response.send_message(
                "⚠️ I don't have permission to assign roles.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Failed to assign role due to an HTTP error: {e}",
                ephemeral=True
            )
            
# Handle Hackathon Role Request
async def handle_get_hackathon_role(interaction):
    embed = discord.Embed(
        title="Get Hackathon Role",
        description=(
            "Only ask to get a role if you are **REGISTERED** and **PARTICIPATING** in the hackathons.\n\n"
            "If you are not registered and not participating in these available hackathons, please do not ask as members will be cross-checked and removed if we find out that users are not participating unless a team member asks so or you are part of the team or would like to help participants.\n\n"
            "If the roles are abused, the user will be muted or face other consequences."
        ),
        color=discord.Color.from_str("#E6E6E6")
    )
    view = View()
    view.add_item(HackathonRoleDropdown())
    await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    try:
        custom_id = interaction.data.get("custom_id")
        if custom_id == "start_setup":
            await handle_start_setup(interaction)
        elif custom_id == "select_sub_roles":
            await handle_select_sub_roles(interaction)
        elif custom_id == "select_ecosystems":
            await handle_select_ecosystems(interaction)
        elif custom_id == "provide_profiles":
            await interaction.response.send_modal(ProfileLinksModal())
        elif custom_id == "agree_terms":
            await handle_agree_terms(interaction)
        elif custom_id == "show_agreement_modal":
            await interaction.response.send_modal(AgreementModal())
        elif custom_id == "get_hackathon_role":
            await handle_get_hackathon_role(interaction)
    except Exception as e:
        logger.error(f"[ERROR] Exception in interaction: {e}")

async def handle_start_setup(interaction):
    view = View()
    view.add_item(PrimaryRoleDropdown())
    await interaction.response.send_message(
        embed=discord.Embed(
            title="Step 1: Select Primary Role",
            description="Please select your primary role from the dropdown below.",
            color=discord.Color.from_str("#0A0A0A")
        ),
        ephemeral=True,
        view=view
    )

async def handle_select_sub_roles(interaction):
    view = View()
    view.add_item(SubRoleDropdown())
    await interaction.response.send_message(
        embed=discord.Embed(
            title="Step 2: Select Sub-Roles",
            description="Choose additional roles that describe your expertise (optional).",
            color=discord.Color.from_str("#0A0A0A")
        ),
        ephemeral=True,
        view=view
    )

async def handle_select_ecosystems(interaction):
    view = View()
    view.add_item(EcosystemDropdown())
    await interaction.response.send_message(
        embed=discord.Embed(
            title="Step 3: Select Ecosystem",
            description="Choose the ecosystem you're most familiar with.",
            color=discord.Color.from_str("#0A0A0A")
        ),
        ephemeral=True,
        view=view
    )

async def handle_agree_terms(interaction):
    embed = discord.Embed(
        title="Step 4: Agree to the Terms",
        description=(
            "**Please review and agree to the following terms before proceeding:**\n\n"
            "1️⃣ **This setup is exclusively for developers, block producers, or those aspiring to actively contribute in these roles.**\n"
            "2️⃣ **By agreeing, you confirm that all information you provide is accurate and truthful.**\n"
            "3️⃣ **Any misuse of roles or submission of false information may result in removal from the server.**\n"
            "4️⃣ **Your participation helps us create a better, stronger community and supports the growth of the Midnight ecosystem.**\n\n"
            "➡️ **Click 'Next' and type 'I Agree' to confirm your understanding and acceptance of these terms.**"
        ),
        color=discord.Color.from_str("#CCCCCC")
    )
    view = View()
    view.add_item(Button(label="Next", style=discord.ButtonStyle.primary, custom_id="show_agreement_modal"))
    await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        logger.error(f"[ERROR] Failed to start the bot: {e}")