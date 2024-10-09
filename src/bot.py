import discord
from discord.ext import commands, tasks
import json
import os
import asyncio

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
    """
    Updates a specific setting (key-value pair) for the given guild ID.
    
    Args:
        guild_id (int): The guild ID whose settings are being updated.
        key (str): The setting key (e.g., 'welcome_channel', 'admin_role').
        value (Any): The value to set for the provided key.
    """
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
    """
    Retrieves the current settings for the given guild ID.

    Args:
        guild_id (int): The guild ID to get the settings for.

    Returns:
        dict: The guild's settings dictionary (JSON format).
    """
    return load_guild_settings(guild_id)


def get_staff_data():
    """
    Retrieves the current staff data from the staff.json file.

    Returns:
        dict: The staff data dictionary (JSON format).
    """
    return load_staff_data()

# Create the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
    """
    Configure a system for the guild. Available systems: welcome_channel, admin_role, suggestion_channel.
    """
    guild_id = ctx.guild.id
    settings = load_guild_settings(guild_id)
    
    if system == "welcomer":
        # Ensure the value is a valid channel mention
        try:
            channel = await commands.TextChannelConverter().convert(ctx, value)
            settings["welcome_channel"] = channel.id
            await ctx.send(f"Welcome channel has been set to {channel.mention}")
        except commands.BadArgument:
            await ctx.send("Invalid channel. Please mention a valid text channel.")

    elif system == "adminrole":
        # Ensure the value is a valid role mention
        try:
            role = await commands.RoleConverter().convert(ctx, value)
            settings["admin_role"] = role.id
            await ctx.send(f"Admin role has been set to {role.name}")
        except commands.BadArgument:
            await ctx.send("Invalid role. Please mention a valid role.")

    elif system == "suggestions":
        # Ensure the value is a valid channel mention
        try:
            channel = await commands.TextChannelConverter().convert(ctx, value)
            settings["suggestion_channel"] = channel.id
            await ctx.send(f"Suggestion channel has been set to {channel.mention}")
        except commands.BadArgument:
            await ctx.send("Invalid channel. Please mention a valid text channel.")
    else:
        await ctx.send("Invalid system. Available systems are: `welcomer`, `adminrole`, `suggestions`.")
    
    # Save updated settings to the guild file
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

    # Create the embed for the suggestion
    embed = discord.Embed(
        title="New Suggestion",
        description=suggestion,
        color=discord.Color.blue()
    )
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    embed.set_footer(text=f"Suggested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

    # Send the suggestion embed in the suggestion channel
    suggestion_message = await suggestion_channel.send(embed=embed)

    # Add reactions to the suggestion message
    await suggestion_message.add_reaction("✅")
    await suggestion_message.add_reaction("⛔")

    # Confirm to the user that the suggestion has been submitted
    await ctx.send(f"Your suggestion has been sent to {suggestion_channel.mention}")

# Command to view current guild settings (Admin only)
@bot.command()
@commands.has_permissions(administrator=True)
async def viewsettings(ctx):
    guild_id = ctx.guild.id
    settings = get_guild_data(guild_id)  # Correctly use get_guild_data here
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
        load_guild_settings(guild_id)  # Reload the guild settings file
        await asyncio.sleep(0.5)  # Simulate time taken to reload settings
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

# Bot startup event to initialize the staff member reloading task
@bot.event
async def on_ready():
    print(f"Bot is online and logged in as {bot.user.name}")
    update_staff_list.start()  # Start the periodic staff update

# Run the bot
TOKEN = "MTI5MzExNDg4ODg2Mzg3OTI1MQ.GqJ5fJ.PLYVpSi9d3kTukeRhJfN7AncngaJf2uRJhDRlo"
bot.run(TOKEN)
