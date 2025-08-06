import discord
import os
import re
from dotenv import load_dotenv
import asyncio
import random
from datetime import datetime
import aiohttp

TIMEZONE_OFFSET = 2  # adjust if needed for your Hogwarts time

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LISTEN_CHANNEL_ID = int(os.getenv("LISTEN_CHANNEL_ID"))
OWNER_ID = int(os.getenv("OWNER_ID"))  # Your Discord ID

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

custom_emoji = "<a:pandarage:1350966430404706335>"
enabled = True
TARGET_SERVER = 1099  # Your server number

# =================== Cute Animal Image Fetching ===================

async def get_random_cute_animal_image_url():
    apis = [
        ("https://random.dog/woof.json", ["url"]),  # Random dog image
        ("https://api.thecatapi.com/v1/images/search?limit=1", [0, "url"]),  # Random cat image
        ("https://randomfox.ca/floof/", ["image"]),  # Random fox image
        ("https://shibe.online/api/shibes?count=1", [0]),  # Random Shiba Inu image
        ("https://shibe.online/api/cats?count=1", [0]),  # Random cat image
        ("https://api.thecatapi.com/v1/images/search", [0, "url"]),  # Random cat image
        ("https://api.thedogapi.com/v1/images/search", [0, "url"]),  # Random dog image
        ("https://some-random-api.com/animal/bear", ["image"]),  # Random bear image
        ("https://cataas.com/cat?json=true", ["url"]),  # Random cat image
        ("https://some-random-api.com/animal/rabbit", ["image"]),  # Random rabbit image
        ("https://some-random-api.com/animal/panda", ["image"]),  # Random panda image
        ("https://some-random-api.com/animal/bird", ["image"]),  # Random bird image
        ("https://some-random-api.com/animal/koala", ["image"]),  # Random koala image
        ("https://www.fishwatch.gov/api/species/random", ["Species Illustration Photo", "src"]),  # Random fish image
    ]

    random.shuffle(apis)

    async with aiohttp.ClientSession() as session:
        for api_url, keys in apis:
            try:
                async with session.get(api_url, timeout=10) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    value = data
                    for key in keys:
                        if isinstance(key, int):
                            value = value[key]
                        else:
                            value = value.get(key)
                        if value is None:
                            break
                    if isinstance(value, str) and value.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                        return value
            except Exception as e:
                print(f"Error fetching from {api_url}: {e}")
                continue
    return None

async def ask_owner_for_image_approval(image_url):
    owner = await client.fetch_user(OWNER_ID)
    embed = discord.Embed(
        title="🐾 Proposed magical creature for today!",
        description="Reply with `yes` to post, `no` to fetch another, `stop` to skip posting today.",
        color=discord.Color.green()
    )
    embed.set_image(url=image_url)
    await owner.send(embed=embed)

    def check(m):
        return m.author.id == OWNER_ID and isinstance(m.channel, discord.DMChannel)

    try:
        msg = await client.wait_for('message', check=check, timeout=160.0)
        return msg.content.strip().lower()
    except asyncio.TimeoutError:
        await owner.send("⏰ Yeh took too long ter reply, so I'm skippin' the creature today.")
        return "stop"

async def post_cute_animal_image(channel):
    hagrid_flavors = [
        "Here's a lil' friend fer yeh, straight from the forest 🪵🦔",
        "Found this one wanderin' near the pumpkins 🐾🎃",
        "Look at this wee beastie, ain't it grand? 🐉",
        "Another magical creature ter brighten yer day ✨",
        "Keep this one quiet, Ministry doesn't know I have it 🦄🤫",
        "Thought yeh might like this one, soft as a puffskein 🪶"
    ]

    while True:
        image_url = await get_random_cute_animal_image_url()
        if not image_url:
            await channel.send("Tried ter get yeh a creature, but the forest's empty today 🐾")
            break

        decision = await ask_owner_for_image_approval(image_url)
        if decision == "yes":
            embed = discord.Embed(
                title=random.choice(hagrid_flavors),
                color=discord.Color.gold()
            )
            embed.set_image(url=image_url)
            await channel.send(embed=embed)
            break
        elif decision == "no":
            continue
        elif decision == "stop":
            await channel.send("No creature today, alright 🐾")
            break
        else:
            await client.get_user(OWNER_ID).send("Please reply with `yes`, `no`, or `stop`.")

# =================== Discord Events ===================

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(status_loop())

@client.event
async def on_message(message):
    global enabled

    if message.author == client.user:
        return
    
    if message.content.lower() == "!enablebot":
        enabled = True
        await message.channel.send("✅ Back to work.")
        return

    if message.content.lower() == "!disablebot":
        enabled = False
        await message.channel.send("⛔ Alright, I'll be takin' a nap.")
        return

    if not enabled:
        return

    # === DM Handling ===
    if message.guild is None:
        if message.author.id != OWNER_ID:
            owner = await client.fetch_user(OWNER_ID)
            await owner.send(f"📨 New DM from **{message.author}** (ID: {message.author.id}):\n{message.content}")
            return

        if message.author.id == OWNER_ID and message.content.startswith("reply"):
            parts = message.content.split(" ", 2)
            if len(parts) < 3:
                await message.channel.send("Usage: reply <USER_ID> <message>")
                return
            try:
                user_id = int(parts[1])
                user_message = parts[2]
                user = await client.fetch_user(user_id)
                await user.send(user_message)
                await message.channel.send(f"✅ Message sent to {user} (ID: {user_id})")
            except Exception as e:
                await message.channel.send(f"❌ Failed to send message: {e}")
            return

     # ============ NEW !fetch implementation ==============
    if message.guild is None and message.author.id == OWNER_ID:
        if message.content.lower() == "!fetch":
            channel = client.get_channel(LISTEN_CHANNEL_ID)

            async def fetch_loop():
                while True:
                    image_url = await get_random_cute_animal_image_url()
                    if not image_url:
                        await message.author.send("Couldn't fetch a creature at the moment 🐾")
                        return

                    decision = await ask_owner_for_image_approval(image_url)
                    if decision == "yes":
                        hagrid_flavors = [
                            "Here's a lil' friend fer yeh, straight from the forest 🪵🦔",
                            "Found this one wanderin' near the pumpkins 🐾🎃",
                            "Look at this wee beastie, ain't it grand? 🐉",
                            "Another magical creature ter brighten yer day ✨",
                            "Keep this one quiet, Ministry doesn't know I have it 🦄🤫",
                            "Thought yeh might like this one, soft as a puffskein 🪶"
                        ]
                        embed = discord.Embed(
                            title=random.choice(hagrid_flavors),
                            color=discord.Color.gold()
                        )
                        embed.set_image(url=image_url)
                        await channel.send(embed=embed)
                        return
                    elif decision == "no":
                        continue
                    elif decision == "stop":
                        await message.author.send("Alright, no creature today 🐾")
                        return
                    else:
                        await message.author.send("Please reply with `yes`, `no`, or `stop`.")
                        continue

            await fetch_loop()
            return
    # ============ End of NEW !fetch ==============
    
    # === Event repost logic ===
    if message.channel.id != LISTEN_CHANNEL_ID:
        return

    if "@Upcoming Events" not in message.content:
        return

    try:
        await message.delete()
    except discord.Forbidden:
        print("Missing permission to delete messages.")
    except discord.HTTPException as e:
        print(f"Failed to delete message: {e}")

    pattern = r"(?:``([^`]*)``\s*For ([^\n]*)EU[^\n]*)"
    matches = re.findall(pattern, message.content, flags=re.MULTILINE)

    found_block = None

    for events, servers in matches:
        server_ranges = re.findall(r"S(\d+)-(\d+)", servers)
        for start, end in server_ranges:
            if int(start) <= TARGET_SERVER <= int(end):
                found_block = f"New events:\n``{events.strip()}``\nFor S{TARGET_SERVER}EU"
                break
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

        # POST CUTE ANIMAL IMAGE AFTER POSTING EVENT
        await post_cute_animal_image(message.channel)

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
