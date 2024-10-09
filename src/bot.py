import discord
from discord.ext import commands, tasks
import json
import os
from dotenv import load_dotenv
import pathlib
import asyncio
import requests
import sys

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

env_path = pathlib.Path('database/.env')
load_dotenv(dotenv_path=env_path)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
last_commit_sha = None  # Initialize the variable for tracking the last commit SHA

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
    bot.remove_command('help')  # Remove the default help command

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
    print(f"Updated staff members: {staff_members}")

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
async def setup(ctx, system: str, value: str):
    guild_id = ctx.guild.id
    settings = load_guild_settings(guild_id)
    
    # Check if the user has administrator permissions or the guild's admin role
    admin_role_id = settings.get("admin_role")
    has_permission = ctx.author.guild_permissions.administrator or (admin_role_id and discord.utils.get(ctx.guild.roles, id=admin_role_id) in ctx.author.roles)

    if not has_permission:
        await ctx.send("You do not have permission to set this up.")
        return

    if not value:
        await ctx.send("You must provide a value for the setup command.")
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

# Start the bot with your token
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)