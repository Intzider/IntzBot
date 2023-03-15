# client.py
import os

import discord
from dotenv import load_dotenv
import vlc

load_dotenv()
TOKEN = os.getenv('TOKEN')
client = discord.Client(intents=discord.Intents.default())


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


client.run(TOKEN)
