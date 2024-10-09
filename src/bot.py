import discord
from discord.ext import commands, tasks
import json
import os
from dotenv import load_dotenv
import pathlib
import asyncio
import requests
import sys
import base64

# Directories for guild settings and staff data
SETTINGS_DIR = "database/guilds/"
STAFF_FILE = "database/data.json"
GITHUB_REPO = "Divine-Development/divine"

# Ensure the guilds directory exists
if not os.path.exists(SETTINGS_DIR):
    os.makedirs(SETTINGS_DIR)

# Ensure the staff file exists, or create it with an empty list
if not os.path.exists(STAFF_FILE):
    with open(STAFF_FILE, 'w') as f:
        json.dump({"staff": []}, f)

# Function to load settings for a specific guild
def load_guild_settings(guild_id):
    file_path = f"{SETTINGS_DIR}{guild_id}.json"
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        return {
            "welcome_channel": None,
            "admin_role": None,
            "suggestion_channel": None,
            "verified": None
        }

# Function to save settings for a specific guild
def save_guild_settings(guild_id, settings):
    file_path = f"{SETTINGS_DIR}{guild_id}.json"
    with open(file_path, 'w') as f:
        json.dump(settings, f, indent=4)

# Function to update guild settings
def update_guild_settings(guild_id, key, value):
    settings = load_guild_settings(guild_id)
    settings[key] = value  # Update the specific setting
    save_guild_settings(guild_id, settings)  # Save the updated settings back to the file

# Function to load staff data
def load_staff_data():
    with open(STAFF_FILE, 'r') as f:
        return json.load(f)

# Function to save staff data
def save_staff_data(staff_data):
    with open(STAFF_FILE, 'w') as f:
        json.dump(staff_data, f, indent=4)

# Function to get guild data
def get_guild_data(guild_id):
    return load_guild_settings(guild_id)

def get_staff_data():
    return load_staff_data()

# Create the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

env_path = pathlib.Path('database/.env')
load_dotenv(dotenv_path=env_path)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
last_commit_sha = None  # Initialize the variable for tracking the last commit SHA

@tasks.loop(seconds=10)
async def check_github_updates():
    global last_commit_sha
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        commits = response.json()
        if commits:
            latest_commit = commits[0]['sha']
            if last_commit_sha is None:
                last_commit_sha = latest_commit  # Initialize on first run
            elif latest_commit != last_commit_sha:
                last_commit_sha = latest_commit  # Update the last known commit SHA
                print("New commit detected! Restarting the bot...")
                await bot.close()  # Close the bot
                os.execv(sys.executable, ['python'] + sys.argv)  # Restart the bot
    else:
        print(f"Failed to fetch commits: {response.status_code} - {response.text}")

# Set up the status loop
@tasks.loop(seconds=20)
async def change_status():
    server_count = len(bot.guilds)  # Get the number of guilds the bot is in

    # Create the activities based on the status messages
    activities = [
        discord.Activity(type=discord.ActivityType.watching, name=f"{server_count} guilds! || !help")
    ]

    # Change the bot's activity to the next one in the list
    current_activity = activities[change_status.current_loop % len(activities)]
    await bot.change_presence(activity=current_activity)

@bot.command()
@commands.is_owner()  # Ensure only the bot owner can use this command
async def checkupdate(ctx):
    global last_commit_sha
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        commits = response.json()
        if commits:
            latest_commit = commits[0]['sha']
            if last_commit_sha is None:
                last_commit_sha = latest_commit  # Initialize on first run
                await ctx.send("Initialized with the latest commit.")
            elif latest_commit != last_commit_sha:
                last_commit_sha = latest_commit  # Update the last known commit SHA
                await ctx.send("New commit detected! Restarting the bot...")
                await bot.close()  # Close the bot
                os.execv(sys.executable, ['python'] + sys.argv)  # Restart the bot
            else:
                await ctx.send("No new commits detected.")
    else:
        await ctx.send(f"Failed to fetch commits: {response.status_code} - {response.text}")

async def update_docs():
    # GitHub repository details
    GITHUB_REPO = "divine-development/divine"
    file_path = "website/index.html"
    branch = "main"

    # GitHub personal access token
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    # Start building the HTML content
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Divine Bot Commands</title>
        <style>
            body, html {
                margin: 0;
                padding: 0;
                height: 100%;
                font-family: Arial, sans-serif;
                color: #fff;
                background: #000 url('https://images.unsplash.com/photo-1519681393784-d120267933ba') no-repeat center center fixed;
                background-size: cover;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: rgba(0, 0, 0, 0.7);
                min-height: 100%;
                box-sizing: border-box;
            }
            h1 {
                text-align: center;
                color: #fff;
                font-size: 3em;
                margin-bottom: 30px;
                animation: glow 2s ease-in-out infinite alternate;
            }
            .command {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .command:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(255, 255, 255, 0.2);
            }
            .command h2 {
                margin-top: 0;
                color: #4da6ff;
            }
            .command-details {
                display: none;
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
            }
            @keyframes glow {
                from {
                    text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px #fff, 0 0 20px #4da6ff, 0 0 35px #4da6ff, 0 0 40px #4da6ff, 0 0 50px #4da6ff, 0 0 75px #4da6ff;
                }
                to {
                    text-shadow: 0 0 10px #fff, 0 0 20px #fff, 0 0 30px #fff, 0 0 40px #4da6ff, 0 0 70px #4da6ff, 0 0 80px #4da6ff, 0 0 100px #4da6ff, 0 0 150px #4da6ff;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Divine Bot Commands</h1>
    """

    # Iterate through all commands
    for command in bot.commands:
        html_content += f"""
            <div class="command" onclick="toggleDetails(this)">
                <h2>{command.name}</h2>
                <div class="command-details">
                    <p><strong>Description:</strong> {command.help or 'No description available.'}</p>
                    <p><strong>Usage:</strong> {bot.command_prefix}{command.name} {command.signature}</p>
                </div>
            </div>
        """

    # Close the HTML content
    html_content += """
        </div>
        <script>
            function toggleDetails(element) {
                var details = element.querySelector('.command-details');
                if (details.style.display === 'none' || details.style.display === '') {
                    details.style.display = 'block';
                } else {
                    details.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """

    try:
        # Get the current file contents
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            current_file = response.json()
            current_sha = current_file['sha']

            # Update the file
            update_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
            update_data = {
                "message": "Update bot commands documentation",
                "content": base64.b64encode(html_content.encode()).decode(),
                "sha": current_sha,
                "branch": branch
            }
            update_response = requests.put(update_url, headers=headers, json=update_data)

            if update_response.status_code == 200:
                print("Documentation updated successfully on GitHub.")
            else:
                print(f"Failed to update documentation. Status code: {update_response.status_code}")
        else:
            print(f"Failed to get current file contents. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while updating the documentation: {str(e)}")

# Bot startup event to initialize the staff member reloading task and status updates
@bot.event
async def on_ready():
    print(f"Bot is online and logged in as {bot.user.name}")
    
    # Start the periodic staff update
    update_staff_list.start()
    
    # Start checking for GitHub updates
    check_github_updates.start()

    # Start changing the bot's status
    change_status.start()

    # Load existing appeals
    load_appeals()

    await update_docs()

    # Create the appeal embed and buttons
    appeal_embed = discord.Embed(
        title="🔔 Appeal Panel",
        description="If you would like to submit an appeal, please click the 'Open Appeal' button below.\n\n✉️ Your appeal will be reviewed promptly.",
        color=discord.Color.blue()
    )
    appeal_embed.set_footer(text="We appreciate your patience during this process.")

    # Create the buttons
    appeal_button = discord.ui.Button(label="Open Appeal", style=discord.ButtonStyle.primary, emoji="📝")
    close_button = discord.ui.Button(label="Close Appeal", style=discord.ButtonStyle.danger, emoji="🔒")

    # Define the button callbacks
    async def appeal_button_callback(interaction: discord.Interaction):
        # Create a modal to gather appeal details
        modal = discord.ui.Modal(title="Appeal Form")

        # Add fields to the modal
        modal.add_item(discord.ui.TextInput(label="Appeal type", placeholder="Server ban, punishment appeal, etc.", style=discord.TextStyle.short))
        modal.add_item(discord.ui.TextInput(label="Reason for appeal", placeholder="Explain why you're appealing", style=discord.TextStyle.paragraph))
        modal.add_item(discord.ui.TextInput(label="Additional information", placeholder="Any other relevant details", style=discord.TextStyle.paragraph))

        # Callback when the modal is submitted
        async def modal_callback(modal_interaction: discord.Interaction):
            appeal_type = modal_interaction.data['components'][0]['components'][0]['value']
            appeal_reason = modal_interaction.data['components'][1]['components'][0]['value']
            additional_info = modal_interaction.data['components'][2]['components'][0]['value']

            appeal_channel = await interaction.guild.create_text_channel(f"appeal-{modal_interaction.user.name}")

            # Send an embed to the new appeal channel
            appeal_details_embed = discord.Embed(
                title="📋 New Appeal Submitted",
                color=discord.Color.green()
            )
            appeal_details_embed.add_field(name="Submitted By", value=f"{modal_interaction.user.mention}", inline=False)
            appeal_details_embed.add_field(name="Appeal Type", value=appeal_type, inline=False)
            appeal_details_embed.add_field(name="Reason for Appeal", value=appeal_reason, inline=False)
            appeal_details_embed.add_field(name="Additional Information", value=additional_info, inline=False)
            appeal_details_embed.add_field(name="Appeal Channel", value=appeal_channel.mention, inline=False)

            # Notify the bot owner and the user who submitted the appeal
            bot_owner = await bot.fetch_user(898255050592366642)  # Replace with your actual bot owner ID
            await appeal_channel.send(f"{bot_owner.mention}, {modal_interaction.user.mention}, here is the appeal:", embed=appeal_details_embed, view=view2)

            # Save the appeal channel ID
            save_appeal(appeal_channel.id, modal_interaction.user.id)

            await modal_interaction.response.send_message("Your appeal has been submitted!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def close_button_callback(interaction: discord.Interaction):
        if interaction.user.id != 898255050592366642:
            await interaction.response.send_message("Only the bot owner can close appeals.", ephemeral=True)
            return

        # Check if the channel is an appeal channel
        appeal_data = load_appeals()
        if str(interaction.channel_id) not in appeal_data:
            await interaction.response.send_message("This is not an appeal channel.", ephemeral=True)
            return

        close_modal = discord.ui.Modal(title="Close Appeal")
        close_modal.add_item(discord.ui.TextInput(label="Reason for closing", style=discord.TextStyle.paragraph))

        async def close_modal_callback(close_modal_interaction: discord.Interaction):
            reason = close_modal_interaction.data['components'][0]['components'][0]['value']
            user_id = appeal_data[str(interaction.channel_id)]
            user = await bot.fetch_user(int(user_id))
            try:
                await user.send(f"Your appeal has been closed. Reason: {reason}")
            except discord.errors.Forbidden:
                await interaction.channel.send(f"Unable to DM {user.mention}. Appeal closed. Reason: {reason}")
            await interaction.channel.delete()
            remove_appeal(interaction.channel_id)

        close_modal.on_submit = close_modal_callback
        await interaction.response.send_modal(close_modal)

    # Assign the callbacks to the buttons
    appeal_button.callback = appeal_button_callback
    close_button.callback = close_button_callback

    # Create a view and add the buttons to it
    view = discord.ui.View(timeout=None)
    view.add_item(appeal_button)
    view2 = discord.ui.View(timeout=None)
    view2.add_item(close_button)

    # Send the appeal panel to a specific channel
    channel = bot.get_channel(1293591350524121172)  # Replace with the ID of the channel you want to send the appeal panel to
    
    # Clear all messages in the channel
    await channel.purge()
    
    # Send the new appeal panel
    await channel.send(embed=appeal_embed, view=view)

def save_appeal(channel_id, user_id):
    appeals = load_appeals()
    appeals[str(channel_id)] = str(user_id)
    with open('appeals.json', 'w') as f:
        json.dump(appeals, f)

def remove_appeal(channel_id):
    appeals = load_appeals()
    appeals.pop(str(channel_id), None)
    with open('appeals.json', 'w') as f:
        json.dump(appeals, f)

def load_appeals():
    if os.path.exists('appeals.json'):
        with open('appeals.json', 'r') as f:
            return json.load(f)
    return {}

# Set up the status loop
@tasks.loop(seconds=10)
async def change_status():
    server_count = len(bot.guilds)  # Get the number of guilds the bot is in
    activity = discord.Activity(type=discord.ActivityType.watching, name=f"{server_count} guilds! || !help")
    await bot.change_presence(activity=activity)

# Load help data from JSON
with open("help.json", "r") as f:
    help_data = json.load(f)

# Custom Help Command
@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title=help_data["title"],
        description=help_data["description"],
        color=discord.Color.blue()
    )
    embed.add_field(name=help_data["field1-name"], value=help_data["field1"], inline=False)

    button = discord.ui.Button(
        label=help_data["button-text"], 
        url=help_data["button-link"], 
        emoji=help_data["button-emoji"]
    )
    view = discord.ui.View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)

# A global variable to store staff list, to be updated periodically
staff_members = []

# Function to periodically update staff members every 20 seconds
@tasks.loop(seconds=20)
async def update_staff_list():
    global staff_members
    staff_data = load_staff_data()
    staff_members = staff_data.get("staff", [])

# Function to check if a user is a staff member
def is_staff(user_id):
    return user_id in staff_members

# Command to add a staff member (Bot owner only)
@bot.command()
@commands.is_owner()
async def addstaff(ctx, user: str):
    staff_data = load_staff_data()

    # Determine if the input is a user ID or a username
    if user.isdigit():  # If input is a number, treat it as a user ID
        user_id = int(user)
        user_obj = ctx.guild.get_member(user_id)
        if user_obj is None:
            await ctx.send("User not found in this guild.")
            return
    else:  # Otherwise, treat it as a username
        user_obj = discord.utils.get(ctx.guild.members, name=user)
        if user_obj is None:
            await ctx.send("User not found in this guild.")
            return

    if user_obj.id not in staff_data['staff']:
        staff_data['staff'].append(user_obj.id)
        save_staff_data(staff_data)
        await ctx.send(f"Added {user_obj.name} to the staff list.")
    else:
        await ctx.send(f"{user_obj.name} is already a staff member.")

# Command to remove a staff member (Bot owner only)
@bot.command()
@commands.is_owner()
async def removestaff(ctx, user: str):
    staff_data = load_staff_data()

    # Determine if the input is a user ID or a username
    if user.isdigit():  # If input is a number, treat it as a user ID
        user_id = int(user)
        user_obj = ctx.guild.get_member(user_id)
        if user_obj is None:
            await ctx.send("User not found in this guild.")
            return
    else:  # Otherwise, treat it as a username
        user_obj = discord.utils.get(ctx.guild.members, name=user)
        if user_obj is None:
            await ctx.send("User not found in this guild.")
            return

    if user_obj.id in staff_data['staff']:
        staff_data['staff'].remove(user_obj.id)
        save_staff_data(staff_data)
        await ctx.send(f"Removed {user_obj.name} from the staff list.")
    else:
        await ctx.send(f"{user_obj.name} is not a staff member.")

# Command to force update the staff list immediately (Bot owner only)
@bot.command()
@commands.is_owner()
async def forcestaffupdate(ctx):
    global staff_members
    staff_data = load_staff_data()
    staff_members = staff_data.get("staff", [])
    await ctx.send(f"Staff list has been force-updated. Current staff: {len(staff_members)} members.")

@bot.command()
async def setup(ctx, system: str = None, *, value: str = None):
    guild_id = ctx.guild.id
    settings = load_guild_settings(guild_id)
    
    # Check if the user has administrator permissions or the guild's admin role
    admin_role_id = settings.get("admin_role")
    has_permission = ctx.author.guild_permissions.administrator or (admin_role_id and discord.utils.get(ctx.guild.roles, id=admin_role_id) in ctx.author.roles)

    if not has_permission:
        await ctx.send("You do not have permission to set this up.")
        return

    if system is None or value is None:
        await ctx.send("You must provide both a system (e.g., 'welcomer', 'adminrole', 'suggestions') and a value.")
        return

    if system == "welcomer":
        try:
            channel = await commands.TextChannelConverter().convert(ctx, value)
            settings["welcome_channel"] = channel.id
            await ctx.send(f"Welcome channel has been set to {channel.mention}")
        except commands.BadArgument:
            await ctx.send("Invalid channel. Please mention a valid text channel.")

    elif system == "adminrole":
        try:
            role = await commands.RoleConverter().convert(ctx, value)
            settings["admin_role"] = role.id
            await ctx.send(f"Admin role has been set to {role.name}")
        except commands.BadArgument:
            await ctx.send("Invalid role. Please mention a valid role.")

    elif system == "suggestions":
        try:
            channel = await commands.TextChannelConverter().convert(ctx, value)
            settings["suggestion_channel"] = channel.id
            await ctx.send(f"Suggestion channel has been set to {channel.mention}")
        except commands.BadArgument:
            await ctx.send("Invalid channel. Please mention a valid text channel.")

    else:
        await ctx.send("Invalid system. Use 'welcomer', 'adminrole', or 'suggestions'.")

    save_guild_settings(guild_id, settings)

# Command to submit a suggestion
@bot.command()
async def suggest(ctx, *, suggestion: str):
    guild_id = ctx.guild.id
    settings = load_guild_settings(guild_id)
    suggestion_channel_id = settings.get("suggestion_channel")

    if suggestion_channel_id is None:
        await ctx.send("Suggestion channel is not set. Please ask an admin to set it using the `setup suggestions` command.")
        return

    suggestion_channel = bot.get_channel(suggestion_channel_id)
    if suggestion_channel is None:
        await ctx.send("Suggestion channel not found. Please ask an admin to reconfigure it.")
        return

    embed = discord.Embed(
        title="New Suggestion",
        description=suggestion,
        color=discord.Color.blue()
    )
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    embed.set_footer(text=f"Suggested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

    suggestion_message = await suggestion_channel.send(embed=embed)
    await suggestion_message.add_reaction("✅")
    await suggestion_message.add_reaction("⛔")

    await ctx.send(f"Your suggestion has been sent to {suggestion_channel.mention}")

# Command to view current guild settings (Admin only)
@bot.command()
@commands.has_permissions(administrator=True)
async def viewsettings(ctx):
    guild_id = ctx.guild.id
    settings = get_guild_data(guild_id)
    welcome_channel = settings.get("welcome_channel", "Not set")
    admin_role = settings.get("admin_role", "Not set")

    welcome_channel = f"<#{welcome_channel}>" if welcome_channel != "Not set" else "Not set"
    admin_role = f"<@&{admin_role}>" if admin_role != "Not set" else "Not set"

    embed = discord.Embed(title=f"Settings for {ctx.guild.name}", color=discord.Color.blue())
    embed.add_field(name="Welcome Channel", value=welcome_channel, inline=False)
    embed.add_field(name="Admin Role", value=admin_role, inline=False)
    await ctx.send(embed=embed)

# Command to reload all guild JSON files and update a progress message (Bot owner only)
@bot.command()
@commands.is_owner()
async def reloadguilds(ctx):
    guild_files = os.listdir(SETTINGS_DIR)
    total_guilds = len(guild_files)
    if total_guilds == 0:
        await ctx.send("No guild settings found to reload.")
        return

    message = await ctx.send(f"Reloading guild settings... 0/{total_guilds}")
    
    for index, guild_file in enumerate(guild_files):
        guild_id = os.path.splitext(guild_file)[0]  # Extract the guild ID from the file name
        load_guild_settings(guild_id)  # Load settings (this is just for demonstration)
        await message.edit(content=f"Reloading guild settings... {index + 1}/{total_guilds}")
        await asyncio.sleep(1)  # Adding a delay to show progress

    await message.edit(content="All guild settings reloaded.")

# Owner-only command to retrieve the JSON settings for a guild
@bot.command()
@commands.is_owner()
async def data(ctx, guild_id: int):
    file_path = f"{SETTINGS_DIR}{guild_id}.json"
    if os.path.exists(file_path):
        await ctx.send(file=discord.File(file_path, f"{guild_id}.json"))
    else:
        await ctx.send(f"No settings file found for guild ID {guild_id}")

# Start the bot with your token
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)