import asyncio
import os

from discord import Intents, Embed
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(intents=Intents().all(),
                   owner_id=270319757167689728,
                   command_prefix=os.getenv('PREFIX'),
                   help_command=None)


class CustomHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = Embed(title="Available commands:")
        embed.add_field(name=f"`/radio [station]`",
                        value="change current station / connect to voice channel",
                        inline=False)
        embed.add_field(name=f"`/disconnect`",
                        value="stop playing and disconnect from voice channel",
                        inline=False)
        embed.add_field(name=f"`/shazam`",
                        value="identify current song (defaults to 10s)",
                        inline=False)
        embed.add_field(name=f"`/shazam [duration]`",
                        value="identify current song with [duration] seconds of listening (between 10 and 20)",
                        inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)


async def load_cogs():
    await bot.load_extension("radio.RadioCog")
    await bot.load_extension("radio.EventsCog")


asyncio.run(load_cogs())
bot.help_command = CustomHelp()
bot.run(os.getenv('TOKEN'))
