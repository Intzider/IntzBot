import logging

from discord.ext import commands
from discord.ext.commands import CommandNotFound

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('Music Bot Ready')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client
        if voice_state is None:
            return

        if len(voice_state.channel.members) == 1:
            await voice_state.disconnect()
            voice_state.cleanup()

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        logger.error(event)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        logger.error(repr(error))


async def setup(bot):
    await bot.add_cog(EventsCog(bot))
