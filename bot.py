import os

from discord import Intents, Embed
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


class CustomHelp(commands.HelpCommand):
    def __init__(self):
        super().__init__()

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


class RadioBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("radio.RadioCog")
        await self.load_extension("radio.EventsCog")


intents = Intents.default()
intents.message_content = True  # needed for prefix (owner) commands

bot = RadioBot(intents=intents,
               owner_id=270319757167689728,
               command_prefix=os.getenv('PREFIX'),
               help_command=CustomHelp())

bot.run(os.getenv('TOKEN'))
