import discord
import os
import re
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LISTEN_CHANNEL_ID = int(os.getenv("LISTEN_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

custom_emoji = "<a:pandarage:1350966430404706335>"
enabled = True
TARGET_SERVER = 1099  # Change as needed

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    global enabled

    if message.author == client.user:
        return

    if message.content.lower() == "!enablebot":
        enabled = True
        await message.channel.send("✅ Event cleaner bot enabled.")
        return

    if message.content.lower() == "!disablebot":
        enabled = False
        await message.channel.send("⛔ Event cleaner bot disabled.")
        return

    if not enabled:
        return

    if message.channel.id != LISTEN_CHANNEL_ID:
        return

    if "@Upcoming Events" not in message.content:
        return

    # Delete immediately while retaining content in memory
    try:
        await message.delete()
    except discord.Forbidden:
        print("Missing permission to delete messages.")
    except discord.HTTPException as e:
        print(f"Failed to delete message: {e}")

    # Parse only EU ranges
    # Matches: ```events``` then "For <server ranges>"
    pattern = r"(?:``([^`]*)``\s*For ([^\n]*)EU[^\n]*)"
    matches = re.findall(pattern, message.content, flags=re.MULTILINE)

    found_block = None

    for events, servers in matches:
        # Extract ranges like S1-1140, S1141-1160, etc.
        server_ranges = re.findall(r"S(\d+)-(\d+)", servers)
        for start, end in server_ranges:
            if int(start) <= TARGET_SERVER <= int(end):
                found_block = f"New events:\n``{events.strip()}``\nFor S{TARGET_SERVER}EU"
                break
        # Handle exact server mentions without ranges, like S1099EU
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

client.run(TOKEN)
