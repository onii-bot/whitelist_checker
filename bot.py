import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient
import os

intents = discord.Intents.all()
intents.members = True

client = commands.Bot(intents=intents, command_prefix=".", case_insensitive=True)

# database
cluster = MongoClient(os.environ["MONGO_TOKEN"])
db = cluster["discord"]
collection = db["dev_whitelist"]


@client.event
async def on_ready():
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)
    print("logged in")


@client.tree.command(name="check", description="Check if your wallet is whitelisted")
@app_commands.describe(wallet_address="Enter your address: ")
async def check(interaction: discord.Interaction, wallet_address: str):
    whitelisted_wallets = collection.find_one({"_id": "whitelist"})["wallets"]
    if wallet_address.lower() in whitelisted_wallets:
        await interaction.response.send_message(f"✅", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌", ephemeral=True)


@client.command()
async def add(ctx):
    if ctx.author.guild_permissions.administrator:
        await ctx.send(
            "Reply with wallets to whitelist (make sure to separate them on each line)"
        )

        def check(m):
            return m.author.id == ctx.author.id

        message = await client.wait_for("message", check=check, timeout=120)
        if not message.author.bot:
            msg = message.content
            new_wallets = list(map(lambda x: x.strip().lower(), msg.splitlines()))
            for wallet in new_wallets:
                if len(wallet) != 42 or wallet[0:2] != "0x":
                    await ctx.send(
                        "Error!! Please only enter valid wallet address and try again"
                    )
                    return
            try:
                whitelisted_wallets = collection.find_one({"_id": "whitelist"})[
                    "wallets"
                ]
                whitelisted_wallets.extend(new_wallets)
                filter = {"_id": "whitelist"}
                newvalues = {"$set": {"wallets": whitelisted_wallets}}
                result = collection.update_one(filter, newvalues)
                await ctx.send("Wallets successfully added")
            except:
                await ctx.send("Database Error")


client.run(os.environ["DISCORD_TOKEN"])
