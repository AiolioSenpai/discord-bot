import discord
import os
import re
from dotenv import load_dotenv
import asyncio
import random
from datetime import datetime

TIMEZONE_OFFSET = 2  # adjust if needed for your Hogwarts time

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LISTEN_CHANNEL_ID = int(os.getenv("LISTEN_CHANNEL_ID"))
OWNER_ID = int(os.getenv("OWNER_ID"))  # Add your Discord user ID here or in .env

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

custom_emoji = "<a:pandarage:1350966430404706335>"
enabled = True
TARGET_SERVER = 1099  # Change as needed

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(status_loop())

@client.event
async def on_message(message):
    global enabled

    if message.author == client.user:
        return

    # === Enable/Disable commands ===
    if message.content.lower() == "!enablebot":
        enabled = True
        await message.channel.send("✅ Back to work.")
        return

    if message.content.lower() == "!disablebot":
        enabled = False
        await message.channel.send("⛔ Alright, I'll be taking a nap.")
        return

    if not enabled:
        return

    # === DM Handling ===
    # Forward all user DMs (except owner's) to the owner
    if message.guild is None:
        if message.author.id != OWNER_ID:
            owner = await client.fetch_user(OWNER_ID)
            await owner.send(f"📨 New DM from **{message.author}** (ID: {message.author.id}):\n{message.content}")
            return

        # Owner sent a DM to the bot - parse reply command
        if message.author.id == OWNER_ID:
            if message.content.startswith("reply"):
                parts = message.content.split(" ", 2)
                if len(parts) < 3:
                    await message.channel.send("Usage: reply <USER_ID> <message>")
                    return
                try:
                    user_id = int(parts[1])
                except ValueError:
                    await message.channel.send("Invalid USER_ID. It must be an integer.")
                    return
                user_message = parts[2]
                try:
                    user = await client.fetch_user(user_id)
                    await user.send(user_message)
                    await message.channel.send(f"✅ Message sent to {user} (ID: {user_id})")
                except Exception as e:
                    await message.channel.send(f"❌ Failed to send message: {e}")
            return

    # === Regular channel message handling ===
    if message.channel.id != LISTEN_CHANNEL_ID:
        return

    if "@Upcoming Events" not in message.content:
        return

    # Delete the original message
    try:
        await message.delete()
    except discord.Forbidden:
        print("Missing permission to delete messages.")
    except discord.HTTPException as e:
        print(f"Failed to delete message: {e}")

    # Parse EU ranges in the message
    pattern = r"(?:``([^`]*)``\s*For ([^\n]*)EU[^\n]*)"
    matches = re.findall(pattern, message.content, flags=re.MULTILINE)

    found_block = None

    for events, servers in matches:
        # Check for ranges like S1-1140, S1141-1160, etc.
        server_ranges = re.findall(r"S(\d+)-(\d+)", servers)
        for start, end in server_ranges:
            if int(start) <= TARGET_SERVER <= int(end):
                found_block = f"New events:\n``{events.strip()}``\nFor S{TARGET_SERVER}EU"
                break
        # Check for exact servers like S1099EU
        exact_servers = re.findall(r"S(\d+)(?!-)\b", servers)
        for server in exact_servers:
            if int(server) == TARGET_SERVER:
                found_block = f"New events:\n``{events.strip()}``\nFor S{TARGET_SERVER}EU"
                break
        if found_block:
            break

    if found_block:
        repost_message = (
            "📢 **Event Update:**\n\n"
            f"Hi! {custom_emoji}\n\n"
            f"{found_block.strip()}\n\n"
            "Credits: ni.nina, founder of Upcoming event server discord\n"
            "@Upcoming Events"
        )
        await message.channel.send(repost_message)
    else:
        print("No relevant EU event block found for the target server.")

async def status_loop():
    day_statuses = [
        "🐉 Feeding Norbert",
        "🌳 Walking in the Forbidden Forest",
        "🪓 Chopping firewood near the hut",
        "🦄 Checking on the unicorns"
    ]

    night_statuses = [
        "🌙 Watching the stars with Fang",
        "💤 Sleeping in the hut",
        "🕯️ Brewing tea by the fireplace"
    ]

    while True:
        hour_utc = datetime.utcnow().hour
        local_hour = (hour_utc + TIMEZONE_OFFSET) % 24

        if 6 <= local_hour < 22:
            status_message = random.choice(day_statuses)
        else:
            status_message = random.choice(night_statuses)

        activity = discord.Game(status_message)
        await client.change_presence(activity=activity)

        await asyncio.sleep(7200)  # update every 2 hours

client.run(TOKEN)
