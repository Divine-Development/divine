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

# === Corrected Update Function ===
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

# === Corrected Get Data Functions ===
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

# Bot startup event to initialize the staff member reloading task
@bot.event
async def on_ready():
    print(f"Bot is online and logged in as {bot.user.name}")
    update_staff_list.start()  # Start the periodic staff update
    check_github_updates.start()  # Start checking for GitHub updates
    bot.remove_command(help)  # Remove the default help command

# Define your custom help command here
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
async def addstaff(ctx, user: discord.User):
    staff_data = load_staff_data()
    if user.id not in staff_data['staff']:
        staff_data['staff'].append(user.id)
        save_staff_data(staff_data)
        await ctx.send(f"Added {user.name} to the staff list.")
    else:
        await ctx.send(f"{user.name} is already a staff member.")

# Command to remove a staff member (Bot owner only)
@bot.command()
@commands.is_owner()
async def removestaff(ctx, user: discord.User):
    staff_data = load_staff_data()
    if user.id in staff_data['staff']:
        staff_data['staff'].remove(user.id)
        save_staff_data(staff_data)
        await ctx.send(f"Removed {user.name} from the staff list.")
    else:
        await ctx.send(f"{user.name} is not a staff member.")

# Command to force update the staff list immediately (Bot owner only)
@bot.command()
@commands.is_owner()
async def forcestaffupdate(ctx):
    global staff_members
    staff_data = load_staff_data()
    staff_members = staff_data.get("staff", [])
    await ctx.send(f"Staff list has been force-updated. Current staff: {len(staff_members)} members.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx, system: str, value: str):
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

    message = await ctx.send(f"Reloading guild settings... 0/{total_guilds} completed.")
    
    for i, guild_file in enumerate(guild_files, start=1):
        guild_id = guild_file.split(".")[0]
        load_guild_settings(guild_id)
        await asyncio.sleep(0.5)
        await message.edit(content=f"Reloading guild settings... {i}/{total_guilds} completed.")

    await message.edit(content=f"Reloading complete! {total_guilds} guild settings reloaded.")

# Owner-only command to retrieve the JSON settings for a guild
@bot.command()
@commands.is_owner()
async def data(ctx, guild_id: int):
    file_path = f"{SETTINGS_DIR}{guild_id}.json"
    if os.path.exists(file_path):
        await ctx.send(file=discord.File(file_path, f"{guild_id}.json"))
    else:
        await ctx.send(f"No settings file found for guild ID {guild_id}")

# Event: When a member joins, send a welcome message (if welcome channel is set)
@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    settings = get_guild_data(guild_id)
    welcome_channel_id = settings.get("welcome_channel")

    if welcome_channel_id:
        try:
            channel = await member.guild.fetch_channel(int(welcome_channel_id))
            if channel:
                await channel.send(f"Welcome to the server, {member.mention}!")
        except discord.errors.NotFound:
            print(f"Welcome channel not found for guild {guild_id}")
        except discord.errors.Forbidden:
            print(f"Bot doesn't have permission to send messages in the welcome channel for guild {guild_id}")
        except Exception as e:
            print(f"Error sending welcome message in guild {guild_id}: {str(e)}")

# Access the TOKEN environment variable
TOKEN = os.getenv('TOKEN')

# GitHub repository and token settings
GITHUB_REPO = "Divine-Development/divine"  # Change to your GitHub repo
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
CHECK_INTERVAL = 60  # Check every 60 seconds
last_commit_sha = None  # To store the last known commit SHA

@tasks.loop(seconds=CHECK_INTERVAL)
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

bot.run(TOKEN)