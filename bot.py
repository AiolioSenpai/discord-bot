import discord
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LISTEN_CHANNEL_ID = int(os.getenv("LISTEN_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

client = discord.Client(intents=intents)

enabled = True

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    global enabled

    # Enable/disable commands
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

    # Check if "@Upcoming Events" text is in the message
    if "@Upcoming Events" in message.content:
        repost_content = message.content

        try:
            await message.delete()
        except discord.Forbidden:
            print("Missing permission to delete messages.")
        except discord.HTTPException as e:
            print(f"Failed to delete message: {e}")

        await message.channel.send(repost_content)

client.run(TOKEN)
