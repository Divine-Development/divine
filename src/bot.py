import os
import json
import asyncio
import sys
import requests
import pathlib
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks

# Directories for guild settings and staff data
SETTINGS_DIR = "database/guilds/"
STAFF_FILE = "database/data.json"
GITHUB_REPO = "Divine-Development/divine"

# Ensure the guilds directory exists
os.makedirs(SETTINGS_DIR, exist_ok=True)

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

# Function to load staff data
def load_staff_data():
    with open(STAFF_FILE, 'r') as f:
        return json.load(f)

# Function to save staff data
def save_staff_data(staff_data):
    with open(STAFF_FILE, 'w') as f:
        json.dump(staff_data, f, indent=4)

# Create the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load environment variables
env_path = pathlib.Path('database/.env')
load_dotenv(dotenv_path=env_path)

# GitHub Token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
last_commit_sha = None  # Initialize the last commit SHA

@tasks.loop(seconds=60)
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

# Bot startup event to initialize the staff member reloading task
@bot.event
async def on_ready():
    print(f"Bot is online and logged in as {bot.user.name}")
    update_staff_list.start()  # Start the periodic staff update
    check_github_updates.start()  # Start checking for GitHub updates
    await bot.remove_command('help')  # Remove the default help command

# Load help data from JSON
with open("help.json", "r") as f:
    help_data = json.load(f)

# Custom Help Command
@bot.command()
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
    print(f"Updated staff members: {staff_members}")

# Command to add a staff member (Bot owner only)
@bot.command()
@commands.is_owner()
async def addstaff(ctx, user: str):
    staff_data = load_staff_data()
    
    # Try to get user by ID or username
    if user.isdigit():
        user_id = int(user)
        user_to_add = ctx.guild.get_member(user_id)
    else:
        user_to_add = discord.utils.get(ctx.guild.members, name=user)

    if user_to_add is None:
        await ctx.send("User not found. Please provide a valid user ID or username.")
        return

    if user_to_add.id not in staff_data['staff']:
        staff_data['staff'].append(user_to_add.id)
        save_staff_data(staff_data)
        await ctx.send(f"Added {user_to_add.name} to the staff list.")
    else:
        await ctx.send(f"{user_to_add.name} is already a staff member.")

# Command to remove a staff member (Bot owner only)
@bot.command()
@commands.is_owner()
async def removestaff(ctx, user: str):
    staff_data = load_staff_data()
    
    # Try to get user by ID or username
    if user.isdigit():
        user_id = int(user)
        user_to_remove = ctx.guild.get_member(user_id)
    else:
        user_to_remove = discord.utils.get(ctx.guild.members, name=user)

    if user_to_remove is None:
        await ctx.send("User not found. Please provide a valid user ID or username.")
        return

    if user_to_remove.id in staff_data['staff']:
        staff_data['staff'].remove(user_to_remove.id)
        save_staff_data(staff_data)
        await ctx.send(f"Removed {user_to_remove.name} from the staff list.")
    else:
        await ctx.send(f"{user_to_remove.name} is not a staff member.")

# Command to force update the staff list immediately (Bot owner only)
@bot.command()
@commands.is_owner()
async def forcestaffupdate(ctx):
    global staff_members
    staff_data = load_staff_data()
    staff_members = staff_data.get("staff", [])
    await ctx.send(f"Staff list has been force-updated. Current staff: {len(staff_members)} members.")

@bot.command()
async def setup(ctx, system: str, value: str):
    # Check for administrator permission or guild's admin role
    settings = load_guild_settings(ctx.guild.id)
    admin_role_id = settings.get("admin_role")
    admin_role = ctx.guild.get_role(admin_role_id)

    if not ctx.author.guild_permissions.administrator and (admin_role is None or admin_role not in ctx.author.roles):
        await ctx.send("You do not have permission to run this command.")
        return

    if not value:
        await ctx.send("Please provide a value for the setup command.")
        return

    guild_id = ctx.guild.id
    settings = load_guild_settings(guild_id)
    
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
        await ctx.send("Invalid system. Available systems are: `welcomer`, `adminrole`, `suggestions`.")
    
    save_guild_settings(guild_id, settings)

# Command to submit a suggestion
@bot.command()
async def suggest(ctx, *, suggestion: str):
    guild_id = ctx.guild.id
    settings = load_guild_settings(guild_id)
    suggestion_channel_id = settings.get("suggestion_channel")

    if suggestion_channel_id:
        suggestion_channel = ctx.guild.get_channel(suggestion_channel_id)
        if suggestion_channel:
            await suggestion_channel.send(f"New suggestion from {ctx.author.mention}: {suggestion}")
            await ctx.send("Your suggestion has been submitted.")
        else:
            await ctx.send("Suggestion channel not found.")
    else:
        await ctx.send("No suggestion channel has been set.")

# Command to view settings
@bot.command()
async def viewsettings(ctx):
    settings = load_guild_settings(ctx.guild.id)
    welcome_channel = f"<#{settings['welcome_channel']}>" if settings["welcome_channel"] else "Not set"
    admin_role = f"<@&{settings['admin_role']}>" if settings["admin_role"] else "Not set"

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

# Start the bot
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)