import asyncio
import os

from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(intents=Intents().all(), command_prefix=os.getenv('PREFIX'))


async def load_cogs():
    await bot.load_extension("radio.RadioCog")
    await bot.load_extension("radio.EventsCog")


async def main():
    await load_cogs()


asyncio.run(main())
bot.run(os.getenv('TOKEN'))
